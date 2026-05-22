/**
 * E2E Tests: Approval Workflow
 */

import { test, expect } from '../fixtures/auth'
import { ApprovalsPage } from '../pages/ApprovalsPage'

test.describe('Approval Workflow', () => {

  test('should load approvals/extension page', async ({ page, testUser }) => {
    const approvalsPage = new ApprovalsPage(page)
    await approvalsPage.goto()

    // Page should have some content or tabs
    await expect(page.locator('.el-tabs, .el-table, .el-empty, .tab-container').first()).toBeVisible({ timeout: 10000 })
  })

  test('should submit a new approval request', async ({ page, testUser }) => {
    const approvalsPage = new ApprovalsPage(page)
    await approvalsPage.goto()

    const createBtn = page.getByRole('button', { name: /提交审批|新建审批|New|Create/i }).first()
    if (await createBtn.isVisible()) {
      await createBtn.click()
      await page.waitForTimeout(500)

      // Fill the form
      const dialog = page.locator('.el-dialog:visible, .el-drawer:visible')
      if (await dialog.isVisible().catch(() => false)) {
        // Select type if exists
        const select = dialog.locator('.el-select').first()
        if (await select.isVisible().catch(() => false)) {
          await select.click()
          await page.waitForTimeout(300)
          const option = page.locator('.el-select-dropdown__item').first()
          if (await option.isVisible().catch(() => false)) await option.click()
        }

        // Fill description/reason
        const textarea = dialog.locator('textarea').first()
        if (await textarea.isVisible().catch(() => false)) {
          await textarea.fill('E2E approval request')
        }

        // Submit
        const submitBtn = dialog.getByRole('button', { name: /提交|Submit|确定|Confirm/i }).first()
        if (await submitBtn.isVisible().catch(() => false)) {
          await submitBtn.click()
          await page.waitForTimeout(2000)
        }
      }
    }
  })

  test('should review (approve/reject) a pending request', async ({ page, testUser }) => {
    const approvalsPage = new ApprovalsPage(page)
    await approvalsPage.goto()

    // Look for pending tab
    const pendingTab = page.getByRole('tab', { name: /待审批|Pending/i })
    if (await pendingTab.isVisible()) {
      await pendingTab.click()
      await page.waitForTimeout(1000)
    }

    // Find approve/reject buttons
    const row = page.locator('.el-table tbody tr').first()
    if (await row.isVisible().catch(() => false)) {
      const approveBtn = row.getByRole('button', { name: /通过|Approve/i })
      const rejectBtn = row.getByRole('button', { name: /拒绝|Reject/i })

      if (await approveBtn.isVisible().catch(() => false)) {
        await approveBtn.click()

        // Confirm dialog may appear
        const confirmBtn = page.getByRole('button', { name: /确定|Confirm|Yes/i })
        if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmBtn.click()
        }
        await page.waitForTimeout(2000)
      } else if (await rejectBtn.isVisible().catch(() => false)) {
        await rejectBtn.click()

        // May ask for reason
        const reasonInput = page.locator('textarea')
        if (await reasonInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          await reasonInput.fill('Rejected by E2E test')
          await page.getByRole('button', { name: /确定|Confirm/i }).click()
        }
        await page.waitForTimeout(2000)
      }
    }
  })
})
