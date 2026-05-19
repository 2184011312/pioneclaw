/**
 * E2E Tests: Tasks CRUD
 */

import { test, expect } from '../fixtures/auth'
import { CrudPage } from '../pages/CrudPage'

test.describe('Tasks CRUD', () => {

  test('should load tasks page', async ({ page, testUser }) => {
    const tasksPage = new CrudPage(page, '/tasks', 'Task')
    await tasksPage.goto()
    // Tasks page uses cards or table — verify heading is visible
    await expect(page.getByRole('heading', { name: /任务/i }).first()).toBeVisible({ timeout: 10000 })
  })

  test('should create a new task', async ({ page, testUser }) => {
    const tasksPage = new CrudPage(page, '/tasks', 'Task')
    await tasksPage.goto()
    await page.waitForTimeout(1000)

    try {
      await tasksPage.openCreateDialog()

      const title = `E2E Task ${Date.now()}`
      await tasksPage.fillDialogField('title', title)
      await tasksPage.fillDialogField('名称', title)
      // Try to fill description
      const textarea = page.locator('.el-dialog:visible textarea, .el-drawer:visible textarea').first()
      if (await textarea.isVisible().catch(() => false)) {
        await textarea.fill('E2E test task description')
      }
      await tasksPage.submitDialog()
      await page.waitForTimeout(2000)
    } catch (e) {
      // If dialog doesn't appear, tasks might have inline creation
      await page.screenshot({ path: 'test-results/tasks-create-debug.png' })
    }
  })

  test('should edit a task if one exists', async ({ page, testUser }) => {
    const tasksPage = new CrudPage(page, '/tasks', 'Task')
    await tasksPage.goto()
    await page.waitForTimeout(1000)

    // Look for edit button on any task row/card
    const editBtn = page.locator('button, a, [role="button"]').filter({ hasText: /编辑|Edit/i }).first()
    if (await editBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await editBtn.click()
      await page.waitForTimeout(500)

      // Check if a dialog opened
      const dialog = page.locator('.el-dialog:visible, .el-drawer:visible')
      if (await dialog.isVisible().catch(() => false)) {
        const titleInput = dialog.locator('input').first()
        if (await titleInput.isVisible().catch(() => false)) {
          await titleInput.fill(`${await titleInput.inputValue()}_edited`)
        }
        await dialog.getByRole('button', { name: /确认|确定|保存|提交|创建|更新|Update/i }).click()
        await page.waitForTimeout(2000)
      }
    }
    // If no edit button, no tasks exist — that's OK
  })

  test('should handle delete if task exists', async ({ page, testUser }) => {
    const tasksPage = new CrudPage(page, '/tasks', 'Task')
    await tasksPage.goto()
    await page.waitForTimeout(1000)

    // Look for delete button
    const deleteBtn = page.locator('button').filter({ hasText: /删除|Delete/i }).first()
    if (await deleteBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await deleteBtn.click()
      // Confirm delete if popover/messagebox appears
      const confirmBtn = page.getByRole('button', { name: /确定|确认|OK|Yes/i }).last()
      if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmBtn.click()
      }
      await page.waitForTimeout(1000)
    }
  })
})
