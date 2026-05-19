/**
 * Generic CRUD Page Object — usable for Agents, Skills, Tasks, Wiki, etc.
 * Assumes Element Plus table + dialog pattern
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class CrudPage extends BasePage {
  readonly pagePath: string
  readonly resourceName: string

  readonly createButton: Locator
  readonly table: Locator
  readonly searchInput: Locator

  constructor(page: Page, pagePath: string, resourceName: string) {
    super(page)
    this.pagePath = pagePath
    this.resourceName = resourceName
    this.createButton = page.getByRole('button', { name: /创建|新建|新增|添加|New|Create|Add/i }).first()
    this.table = page.locator('.el-table, table').first()
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="Search"]').first()
  }

  async goto() {
    await this.navigate(this.pagePath)
  }

  /** Click create button and wait for dialog */
  async openCreateDialog() {
    await this.createButton.click()
    await this.page.waitForSelector('.el-dialog, .el-drawer', { state: 'visible', timeout: 5000 })
  }

  /** Fill a form field by its label inside the active dialog/drawer */
  async fillDialogField(label: string, value: string) {
    const dialog = this.page.locator('.el-dialog:visible, .el-drawer:visible').first()
    // Try textbox role first (accessible name), then fallback to placeholder match
    const textbox = dialog.getByRole('textbox', { name: new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) })
    const textboxCount = await textbox.count()
    if (textboxCount > 0) {
      await textbox.first().fill(value)
    } else {
      // Fallback: find input near label text
      const input = dialog.locator('input').first()
      await input.fill(value)
    }
  }

  /** Submit the dialog form */
  async submitDialog() {
    const dialog = this.page.locator('.el-dialog:visible, .el-drawer:visible').first()
    await dialog.getByRole('button', { name: /确认|确定|保存|提交|创建|更新|Confirm|OK|Save|Submit|Create|Update/i }).click()
  }

  /** Cancel the dialog */
  async cancelDialog() {
    const dialog = this.page.locator('.el-dialog:visible, .el-drawer:visible').first()
    await dialog.getByRole('button', { name: /取消|Cancel/i }).click()
  }

  /** Edit a row by matching any column text */
  async editRow(containsText: string) {
    const row = this.table.locator('tr', { hasText: containsText }).first()
    await row.scrollIntoViewIfNeeded()
    await row.getByRole('button', { name: /编辑|Edit/i }).click()
    await this.page.waitForSelector('.el-dialog:visible, .el-drawer:visible', { state: 'visible', timeout: 5000 })
  }

  /** Delete a row by matching any column text */
  async deleteRow(containsText: string) {
    const row = this.table.locator('tr', { hasText: containsText }).first()
    await row.scrollIntoViewIfNeeded()
    await row.getByRole('button', { name: /删除|Delete/i }).click()
    // Confirm the ElMessageBox
    const confirmBtn = this.page.getByRole('button', { name: /确定|确认|OK|Yes/i }).last()
    if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmBtn.click()
    }
  }

  /** Assert table contains text */
  async expectRowVisible(text: string) {
    await expect(this.table.locator('tr', { hasText: text }).first()).toBeVisible({ timeout: 5000 })
  }

  /** Assert table does NOT contain text */
  async expectRowNotVisible(text: string) {
    await expect(this.table.locator('tr', { hasText: text }).first()).not.toBeVisible({ timeout: 5000 })
  }

  /** Count rows in the table body */
  async getRowCount(): Promise<number> {
    return this.table.locator('tbody tr').count()
  }
}
