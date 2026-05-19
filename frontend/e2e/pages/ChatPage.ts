/**
 * Chat / Agent Conversation Page Object
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class ChatPage extends BasePage {
  readonly messageInput: Locator
  readonly sendButton: Locator
  readonly conversationList: Locator
  readonly newChatButton: Locator
  readonly messageList: Locator

  constructor(page: Page) {
    super(page)
    this.messageInput = page.locator('.chat-input-area textarea, .message-input textarea, [contenteditable="true"]').first()
    this.sendButton = page.getByRole('button', { name: /发送|Send|→|submit/i }).first()
    this.conversationList = page.locator('.chat-sidebar, .conversation-list').first()
    this.newChatButton = page.getByRole('button', { name: /新对话|New Chat|plus/i }).first()
    this.messageList = page.locator('.chat-messages, .messages-wrapper').first()
  }

  async goto() {
    await this.navigate('/chat')
  }

  async sendMessage(text: string) {
    // Type into the input and send
    await this.messageInput.fill(text)
    await this.sendButton.click()
  }

  /** Wait for agent response to complete (loading spinner gone) */
  async waitForResponse(timeout = 30000) {
    try {
      await this.page.waitForFunction(
        () => {
          const loaders = document.querySelectorAll('.el-loading-spinner, .loading, .el-loading-mask')
          return loaders.length === 0
        },
        { timeout }
      )
    } catch {
      // Loading may not have been visible
    }
    // Brief settle after loading
    await this.page.waitForTimeout(500)
  }

  /** Get the last assistant message text */
  async getLastAssistantMessage(): Promise<string> {
    const messages = this.page.locator('.message-bubble-wrapper.assistant .message-content')
    const last = messages.last()
    await last.waitFor({ state: 'visible', timeout: 30000 })
    return (await last.textContent()) || ''
  }

  /** Start a new conversation */
  async newConversation() {
    await this.newChatButton.click()
    await this.page.waitForTimeout(500)
  }

  /** Get tool call bubbles in the last assistant message */
  getToolCallBubbles(): Locator {
    return this.page.locator('.tool-call-bubble')
  }

  /** Get tool call items (individual tool results) */
  getToolCallItems(): Locator {
    return this.page.locator('.tool-call-item')
  }

  /** Get active tool status bar */
  getToolStatusBar(): Locator {
    return this.page.locator('.tools-status')
  }

  /** Get individual tool status items */
  getToolStatusItems(): Locator {
    return this.page.locator('.tool-status-item')
  }

  /** Wait for any tool call bubble to appear (SSE tool_result) */
  async waitForToolCalls(timeout = 30000): Promise<boolean> {
    try {
      await this.page.locator('.tool-call-bubble').first().waitFor({ state: 'visible', timeout })
      return true
    } catch {
      return false
    }
  }

  /** Wait for tool status bar to appear (WebSocket tool events) */
  async waitForToolStatus(timeout = 30000): Promise<boolean> {
    try {
      await this.page.locator('.tools-status').first().waitFor({ state: 'visible', timeout })
      return true
    } catch {
      return false
    }
  }

  /** Wait for streaming to finish (no more loading indicators) */
  async waitForStreamEnd(timeout = 60000) {
    try {
      await this.page.waitForFunction(
        () => {
          const loaders = document.querySelectorAll('.el-loading-spinner, .loading, .el-loading-mask')
          return loaders.length === 0
        },
        { timeout }
      )
    } catch {
      // Loading may not have been visible
    }
    await this.page.waitForTimeout(1000)
  }
}
