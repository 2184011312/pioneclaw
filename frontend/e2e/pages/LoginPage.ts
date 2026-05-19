/**
 * Login / Register Page Object
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class LoginPage extends BasePage {
  readonly usernameInput: Locator
  readonly passwordInput: Locator
  readonly loginButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    super(page)
    this.usernameInput = page.locator('input[placeholder*="用户名"], input[placeholder*="Username"], input[placeholder*="用户"], .el-input input').first()
    this.passwordInput = page.locator('input[type="password"]').first()
    this.loginButton = page.getByRole('button', { name: /登录|Login|登 录/i })
    this.errorMessage = page.locator('.el-message--error .el-message__content, .el-form-item__error, .el-alert--error').first()
  }

  async goto() {
    await this.navigate('/login')
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username)
    await this.passwordInput.fill(password)
    await this.loginButton.click()
  }

  /** Expect to be redirected to dashboard after login */
  async expectLoginSuccess() {
    await this.page.waitForURL(/\/dashboard/, { timeout: 10000 })
  }
}

export class RegisterPage extends BasePage {
  readonly usernameInput: Locator
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly registerButton: Locator

  constructor(page: Page) {
    super(page)
    this.usernameInput = page.locator('input[placeholder*="用户名"], input[placeholder*="Username"]').first()
    this.emailInput = page.locator('input[type="email"], input[placeholder*="邮箱"], input[placeholder*="Email"]').first()
    this.passwordInput = page.locator('input[type="password"]').first()
    this.registerButton = page.getByRole('button', { name: /注册|Register|注 册/i })
  }

  async goto() {
    await this.navigate('/login')
    await this.page.getByText(/注册|Register/i).first().click()
    await this.page.waitForTimeout(500)
  }

  async register(username: string, email: string, password: string) {
    await this.usernameInput.fill(username)
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.registerButton.click()
  }
}
