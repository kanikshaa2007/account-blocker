import { reactive } from 'vue'

let seq = 0
export const toasts = reactive([])

export function toast(message, tone = 'info', timeout = 4200) {
  const id = ++seq
  toasts.push({ id, message, tone })
  setTimeout(() => {
    const i = toasts.findIndex((t) => t.id === id)
    if (i >= 0) toasts.splice(i, 1)
  }, timeout)
}
