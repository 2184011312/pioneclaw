/**
 * E2E Tests: Login & Register flow
 */

import { test, expect } from '../fixtures/auth'
import { LoginPage } from '../pages/LoginPage'

test.describe('Login Flow', () => {

  test('should show login page', async ({ page }) => {
    const loginPage = new LoginPage(page)
    await loginPage.goto()
    await expect(loginPage.usernameInput).toBeVisible()
  })

  test('should login with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page)
    await loginPage.goto()
    await loginPage.login('admin', 'admin123')
    await loginPage.expectLoginSuccess()
  })

  test('should not redirect on wrong password', async ({ page }) => {
    const loginPage = new LoginPage(page)
    await loginPage.goto()
    await loginPage.login('admin', 'wrong_password_xyz')
    // Should stay on login page (error handled silently by interceptor)
    await page.waitForTimeout(2000)
    expect(page.url()).toContain('/login')
  })

  test('should redirect to login when accessing protected page without token', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForURL(/\/login/, { timeout: 10000 })
  })
})
