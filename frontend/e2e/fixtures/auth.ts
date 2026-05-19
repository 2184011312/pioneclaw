/**
 * E2E Auth fixtures — login via API for speed, not through UI
 */

import { test as base, request, APIRequestContext } from '@playwright/test'

interface TestUser {
  username: string
  password: string
  token: string
  userId: number
  email: string
}

interface AuthFixtures {
  /** A freshly registered test user with token set in localStorage */
  testUser: TestUser
  /** An admin user (super_admin) token */
  adminToken: string
}

// Shared API context for user creation
let apiCtx: APIRequestContext | null = null

export const test = base.extend<AuthFixtures>({
  testUser: [
    async ({ page }, use) => {
      // Create API context for backend calls
      if (!apiCtx) {
        apiCtx = await request.newContext({ baseURL: 'http://127.0.0.1:8000' })
      }

      const suffix = Date.now()
      const user: TestUser = {
        username: `e2e_user_${suffix}`,
        password: 'E2eTest123!',
        token: '',
        userId: 0,
        email: `e2e_${suffix}@test.com`,
      }

      // Register
      const registerResp = await apiCtx.post('/api/auth/register', {
        data: {
          username: user.username,
          email: user.email,
          password: user.password,
          display_name: 'E2E Test User',
        },
      })

      if (registerResp.ok()) {
        const body = await registerResp.json()
        user.userId = body.id
      } else {
        // Might already exist — try login
        const loginResp = await apiCtx.post('/api/auth/login', {
          data: { username: user.username, password: user.password },
        })
        if (loginResp.ok()) {
          const body = await loginResp.json()
          user.token = body.access_token
          user.userId = body.user_id || 0
        }
      }

      // Login to get token
      const loginResp = await apiCtx.post('/api/auth/login', {
        data: { username: user.username, password: user.password },
      })
      if (loginResp.ok()) {
        const body = await loginResp.json()
        user.token = body.access_token
      }

      // Set token in localStorage before page loads
      await page.goto('/')
      await page.evaluate((token) => {
        localStorage.setItem('token', token)
      }, user.token)

      await use(user)

      // Cleanup: delete the test user and their auto-created org
      const cleanupCtx = await request.newContext({ baseURL: 'http://127.0.0.1:8000' })
      try {
        // Login as admin
        const adminResp = await cleanupCtx.post('/api/auth/login', {
          data: { username: 'admin', password: 'admin123' },
        })
        if (adminResp.ok()) {
          const adminBody = await adminResp.json()
          const adminToken = adminBody.access_token

          // Delete user first (required before org can be deleted)
          if (user.userId) {
            await cleanupCtx.delete(`/api/users/${user.userId}`, {
              headers: { Authorization: `Bearer ${adminToken}` },
            })
          }

          // Delete org by code (org code === username for auto-created orgs)
          const orgsResp = await cleanupCtx.get('/api/organizations/simple', {
            headers: { Authorization: `Bearer ${adminToken}` },
          })
          if (orgsResp.ok()) {
            const orgs = await orgsResp.json()
            for (const org of orgs) {
              if (org.code === user.username) {
                await cleanupCtx.delete(`/api/organizations/${org.id}`, {
                  headers: { Authorization: `Bearer ${adminToken}` },
                })
              }
            }
          }
        }
      } catch {
        // Best-effort cleanup — ignore failures
      } finally {
        await cleanupCtx.dispose()
      }
    },
    { scope: 'test' },
  ],

  adminToken: [
    async ({}, use) => {
      if (!apiCtx) {
        apiCtx = await request.newContext({ baseURL: 'http://127.0.0.1:8000' })
      }

      // Try to login as default super_admin
      const resp = await apiCtx.post('/api/auth/login', {
        data: { username: 'admin', password: 'admin123' },
      })

      let token = ''
      if (resp.ok()) {
        const body = await resp.json()
        token = body.access_token
      } else {
        // Try to register admin
        await apiCtx.post('/api/auth/register', {
          data: {
            username: 'admin',
            email: 'admin@pioneclaw.com',
            password: 'admin123',
            display_name: 'Admin',
          },
        })
        const loginResp = await apiCtx.post('/api/auth/login', {
          data: { username: 'admin', password: 'admin123' },
        })
        if (loginResp.ok()) {
          const body = await loginResp.json()
          token = body.access_token
        }
      }

      await use(token)
    },
    { scope: 'worker' },
  ],
})

export { expect } from '@playwright/test'
