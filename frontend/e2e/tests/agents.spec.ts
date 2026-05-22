/**
 * E2E Tests: Agents CRUD
 */

import { test, expect } from '../fixtures/auth'
import { CrudPage } from '../pages/CrudPage'

test.describe('Agents CRUD', () => {

  test('should list agents', async ({ page, testUser }) => {
    const agentsPage = new CrudPage(page, '/agents', 'Agent')
    await agentsPage.goto()
    await expect(agentsPage.table).toBeVisible()
  })

  test('should create, edit and delete an agent', async ({ page, testUser }) => {
    test.setTimeout(120000)
    const agentsPage = new CrudPage(page, '/agents', 'Agent')
    await agentsPage.goto()

    // --- Create ---
    const name = `E2E_Agent_${Date.now()}`
    await agentsPage.openCreateDialog()
    await agentsPage.fillDialogField('名称', name)
    await agentsPage.fillDialogField('显示名称', name)
    const desc = page.locator('.el-dialog:visible textarea, .el-drawer:visible textarea').first()
    if (await desc.isVisible().catch(() => false)) await desc.fill('E2E test')
    await agentsPage.submitDialog()
    await page.waitForTimeout(2000)

    // --- Verify created ---
    const row = agentsPage.table.locator('tr', { hasText: name }).first()
    await row.scrollIntoViewIfNeeded()
    await expect(row).toBeVisible({ timeout: 5000 })

    // --- Edit ---
    await row.getByRole('button', { name: /编辑|Edit/i }).click()
    await page.waitForSelector('.el-dialog:visible, .el-drawer:visible', { state: 'visible', timeout: 5000 })
    const dialog = page.locator('.el-dialog:visible, .el-drawer:visible').first()
    const dispInput = dialog.getByRole('textbox', { name: /显示名称/i })
    if ((await dispInput.count()) > 0) await dispInput.first().fill(`${name}_edited`)
    await dialog.getByRole('button', { name: /确认|确定|保存|提交|创建|更新|Update/i }).click()
    await page.waitForTimeout(2000)

    // --- Delete ---
    const deleteBtn = agentsPage.table.locator('tr', { hasText: name }).first().getByRole('button', { name: /删除|Delete/i })
    await deleteBtn.scrollIntoViewIfNeeded()
    await deleteBtn.click()
    const confirmBtn = page.getByRole('button', { name: /确定|确认|OK|Yes/i }).last()
    if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmBtn.click()
    }
    await page.waitForTimeout(2000)
  })
})
