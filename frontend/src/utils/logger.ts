/**
 * 条件日志工具 — 仅开发模式输出 debug 级别日志
 * 生产环境只保留 console.error（错误上报）
 */

const isDev = import.meta.env.DEV

export const logger = {
  log(...args: unknown[]): void {
    if (isDev) console.log(...args)
  },
  warn(...args: unknown[]): void {
    if (isDev) console.warn(...args)
  },
  info(...args: unknown[]): void {
    if (isDev) console.info(...args)
  },
  /** error 始终输出（用于错误上报追踪） */
  error(...args: unknown[]): void {
    console.error(...args)
  },
}
