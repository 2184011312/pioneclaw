/**
 * Base Page Object — shared helpers for all pages
 */

import { Page, Locator } from '@playwright/test'

export class BasePage {
  readonly page: Page
  readonly toast: Locator

  constructor(page: Page) {
    this.page = page
    this.toast = page.locator('.el-message, .el-notification')
  }

  /** Wait for page to fully load (network idle) */
  async waitForReady() {
    await this.page.waitForLoadState('networkidle')
  }

  /** Get success/error toast text */
  async getToastText(): Promise<string> {
    const toast = this.page.locator('.el-message__content, .el-notification__content').first()
    await toast.waitFor({ state: 'visible', timeout: 5000 })
    return (await toast.textContent()) || ''
  }

  /** Navigate to a route */
  async navigate(path: string) {
    await this.page.goto(path)
    await this.waitForReady()
  }

  /** Check if a dialog/modal is visible */
  async isDialogVisible(): Promise<boolean> {
    return this.page.locator('.el-dialog, .el-drawer').first().isVisible()
  }

  /** Close current dialog */
  async closeDialog() {
    await this.page.locator('.el-dialog__close, .el-drawer__close').first().click()
  }

  /** Click a button by text */
  async clickButton(label: string) {
    await this.page.getByRole('button', { name: label }).click()
  }

  /** Fill a labeled form field */
  async fillField(label: string, value: string) {
    await this.page.getByLabel(label).fill(value)
  }
}
