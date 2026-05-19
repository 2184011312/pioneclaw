/**
 * E2E Tests: Skills CRUD
 */

import { test, expect } from '../fixtures/auth'
import { CrudPage } from '../pages/CrudPage'

test.describe('Skills CRUD', () => {

  test('should list skills', async ({ page, testUser }) => {
    const skillsPage = new CrudPage(page, '/skills', 'Skill')
    await skillsPage.goto()
    await expect(skillsPage.table).toBeVisible()
  })

  test('should create, edit and delete a skill', async ({ page, testUser }) => {
    test.setTimeout(120000)
    const skillsPage = new CrudPage(page, '/skills', 'Skill')
    await skillsPage.goto()

    // --- Create ---
    const name = `e2e_skill_${Date.now()}`
    await skillsPage.openCreateDialog()

    // Fill name field
    const dialog = page.locator('.el-dialog:visible, .el-drawer:visible').first()
    const nameInput = dialog.getByRole('textbox', { name: /名称/ }).first()
    if ((await nameInput.count()) > 0) {
      await nameInput.fill(name)
    } else {
      await dialog.locator('input').first().fill(name)
    }

    // Fill display name
    const displayInput = dialog.getByRole('textbox', { name: /显示名称/ })
    if ((await displayInput.count()) > 0) await displayInput.fill(name)

    // Fill content
    const textarea = dialog.locator('textarea').first()
    if (await textarea.isVisible().catch(() => false)) {
      await textarea.fill('print("hello e2e")')
    }

    await dialog.getByRole('button', { name: /确认|确定|保存|提交|创建|更新|Update/i }).click()
    await page.waitForTimeout(2000)

    // --- Verify created ---
    const row = skillsPage.table.locator('tr', { hasText: name }).first()
    await row.scrollIntoViewIfNeeded()
    await expect(row).toBeVisible({ timeout: 5000 })

    // --- Edit ---
    await row.getByRole('button', { name: /编辑|Edit/i }).click()
    await page.waitForSelector('.el-dialog:visible, .el-drawer:visible', { state: 'visible', timeout: 5000 })
    const editDialog = page.locator('.el-dialog:visible, .el-drawer:visible').first()
    const disp2 = editDialog.getByRole('textbox', { name: /显示名称/ })
    if ((await disp2.count()) > 0) await disp2.first().fill(`${name}_updated`)
    await editDialog.getByRole('button', { name: /确认|确定|保存|提交|创建|更新|Update/i }).click()
    await page.waitForTimeout(2000)

    // --- Delete ---
    const deleteRow = skillsPage.table.locator('tr', { hasText: name }).first()
    const deleteBtn = deleteRow.getByRole('button', { name: /删除|Delete/i })
    await deleteRow.scrollIntoViewIfNeeded()
    if (await deleteBtn.isVisible().catch(() => false)) {
      await deleteBtn.click()
      const confirmBtn = page.getByRole('button', { name: /确定|确认|OK|Yes/i }).last()
      if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmBtn.click()
      }
    }
    await page.waitForTimeout(2000)
  })
})
