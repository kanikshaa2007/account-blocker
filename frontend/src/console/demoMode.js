import { ref } from 'vue'

const KEY = 'mf-console-demo'
const flag = ref(localStorage.getItem(KEY) !== 'off')

export function isDemoMode() { return flag }
export function setDemoMode(on) {
  flag.value = on
  localStorage.setItem(KEY, on ? 'on' : 'off')
}
