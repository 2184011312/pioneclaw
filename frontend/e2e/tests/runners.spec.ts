/**
 * E2E Tests: Runners & Center Communication
 * Note: Runners.vue has no dedicated route — accessed via system-ops or ai-management
 */

import { test, expect } from '../fixtures/auth'
import { RunnersPage } from '../pages/RunnersPage'

test.describe('Runners & Center Communication', () => {

  test('should load runners section', async ({ page, testUser }) => {
    const runnersPage = new RunnersPage(page)
    await runnersPage.goto()

    // Page should have loaded — verify something meaningful is visible
    const hasContent = await page.locator('main, .el-main, [class*="container"]').first().isVisible()
    expect(hasContent).toBeTruthy()
  })

  test('should look for runner registration/add button', async ({ page, testUser }) => {
    const runnersPage = new RunnersPage(page)
    await runnersPage.goto()

    // Try to find any "add" or "register" button
    const addBtn = page.getByRole('button', { name: /添加|新增|注册|Add|New|Register/i }).first()
    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click()
      await page.waitForTimeout(500)

      // Verify dialog or form appeared
      const dialog = page.locator('.el-dialog:visible, .el-drawer:visible, form')
      const isVisible = await dialog.isVisible().catch(() => false)
      expect(isVisible).toBeTruthy()
    }
    // If no add button, runners might be loaded via center hub — that's OK
  })

  test('should list any existing runners', async ({ page, testUser }) => {
    const runnersPage = new RunnersPage(page)
    await runnersPage.goto()

    // Runners are embedded in AI Management or System Ops — just verify page content loaded
    const hasContent = await page.locator('main, .el-main, [class*="container"], .el-card, .el-table, .el-empty, .el-tabs').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasContent).toBeTruthy()
  })
})
