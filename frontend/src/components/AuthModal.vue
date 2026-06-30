<script setup>
import { ref, inject, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const t = inject('t')
const API_BASE = ''

const emit = defineEmits(['close', 'authenticated'])

// ─── State ────────────────────────────────────────────────────────────────────
const mode = ref('login') // 'login' | 'register'
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)
const touched = ref({ email: false, password: false, confirm: false })

const isLogin = computed(() => mode.value === 'login')

// ─── Real-time field validation ────────────────────────────────────────────────
const emailValid = computed(() => {
  if (!touched.value.email && !email.value) return null
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)
})

const passwordValid = computed(() => {
  if (!touched.value.password && !password.value) return null
  return password.value.length >= 8
})

const confirmValid = computed(() => {
  if (!touched.value.confirm && !confirmPassword.value) return null
  if (!confirmPassword.value) return null
  return password.value === confirmPassword.value
})

// ─── ESC to close ─────────────────────────────────────────────────────────────
function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

// Reset touched on mode switch
watch(mode, () => {
  error.value = ''
  confirmPassword.value = ''
  touched.value = { email: false, password: false, confirm: false }
})

// ─── Submit ───────────────────────────────────────────────────────────────────
function validate() {
  if (!emailValid.value) {
    error.value = t.value.auth_error_invalid_email
    return false
  }
  if (!passwordValid.value) {
    error.value = t.value.auth_error_password_length
    return false
  }
  if (!isLogin.value && !confirmValid.value) {
    error.value = t.value.auth_error_password_match
    return false
  }
  return true
}

async function submit() {
  error.value = ''
  // Mark all as touched
  touched.value = { email: true, password: true, confirm: true }
  if (!validate()) return

  loading.value = true
  const endpoint = isLogin.value ? '/api/auth/login' : '/api/auth/register'
  const body = { email: email.value.trim().toLowerCase(), password: password.value }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()

    if (!res.ok) {
      error.value = data.detail || t.value.error_network
      return
    }

    if (data.success && data.token) {
      localStorage.setItem('auth_token', data.token)
      emit('authenticated', { token: data.token, user: data.user })
    }
  } catch {
    error.value = t.value.error_network
  } finally {
    loading.value = false
  }
}

function switchMode() {
  mode.value = isLogin.value ? 'register' : 'login'
}
</script>

<template>
  <div class="modal-overlay">
    <div class="modal-card">
      <button class="modal-close" @click="$emit('close')" aria-label="Close">
        <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"/>
        </svg>
      </button>

      <h2 class="modal-title">{{ isLogin ? t.auth_sign_in : t.auth_register }}</h2>

      <!-- Switch link -->
      <p class="modal-desc">
        {{ isLogin ? t.auth_switch_to_register : t.auth_switch_to_login }}
        <a href="#" class="modal-switch" @click.prevent="switchMode">
          {{ isLogin ? t.auth_register : t.auth_sign_in }}
        </a>
      </p>

      <!-- Server error -->
      <div v-if="error" class="modal-error">
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" class="modal-error-icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/></svg>
        <span>{{ error }}</span>
      </div>

      <!-- Form -->
      <form class="modal-form" @submit.prevent="submit">
        <!-- Email -->
        <div class="form-group">
          <label class="form-label" for="auth-email">{{ t.auth_email }}</label>
          <div class="input-wrap">
            <input
              id="auth-email"
              v-model="email"
              class="form-input"
              :class="{
                'input-valid': touched.email && emailValid === true,
                'input-invalid': touched.email && emailValid === false
              }"
              type="email"
              :placeholder="t.auth_email"
              autocomplete="email"
              @blur="touched.email = true"
            />
            <span v-if="touched.email && emailValid === true" class="input-icon input-icon-ok">&#10003;</span>
            <span v-if="touched.email && emailValid === false" class="input-icon input-icon-err">&#10007;</span>
          </div>
          <p v-if="touched.email && emailValid === false" class="field-hint field-hint-err">{{ t.auth_error_invalid_email }}</p>
        </div>

        <!-- Password -->
        <div class="form-group">
          <label class="form-label" for="auth-password">{{ t.auth_password }}</label>
          <div class="input-wrap">
            <input
              id="auth-password"
              v-model="password"
              class="form-input"
              :class="{
                'input-valid': touched.password && passwordValid === true,
                'input-invalid': touched.password && passwordValid === false
              }"
              type="password"
              :placeholder="t.auth_password"
              :autocomplete="isLogin ? 'current-password' : 'new-password'"
              @blur="touched.password = true"
            />
            <span v-if="touched.password && passwordValid === true" class="input-icon input-icon-ok">&#10003;</span>
            <span v-if="touched.password && passwordValid === false" class="input-icon input-icon-err">&#10007;</span>
          </div>
          <p class="field-hint">至少 8 个字符</p>
          <p v-if="touched.password && passwordValid === false" class="field-hint field-hint-err">{{ t.auth_error_password_length }}</p>
        </div>

        <!-- Confirm Password -->
        <div v-if="!isLogin" class="form-group">
          <label class="form-label" for="auth-confirm">{{ t.auth_confirm_password }}</label>
          <div class="input-wrap">
            <input
              id="auth-confirm"
              v-model="confirmPassword"
              class="form-input"
              :class="{
                'input-valid': touched.confirm && confirmValid === true,
                'input-invalid': touched.confirm && confirmValid === false
              }"
              type="password"
              :placeholder="t.auth_confirm_password"
              autocomplete="new-password"
              @blur="touched.confirm = true"
            />
            <span v-if="touched.confirm && confirmValid === true" class="input-icon input-icon-ok">&#10003;</span>
            <span v-if="touched.confirm && confirmValid === false" class="input-icon input-icon-err">&#10007;</span>
          </div>
          <p v-if="touched.confirm && confirmValid === false" class="field-hint field-hint-err">{{ t.auth_error_password_match }}</p>
          <p v-if="touched.confirm && confirmValid === true" class="field-hint field-hint-ok">密码一致</p>
        </div>

        <button type="submit" class="form-submit" :disabled="loading">
          <span v-if="!loading">{{ isLogin ? t.auth_login_btn : t.auth_register_btn }}</span>
          <span v-else class="spinner"></span>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 200;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal-card {
  position: relative;
  background: #ffffff;
  border-radius: 20px;
  padding: 40px 36px;
  width: 100%; max-width: 420px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05);
  animation: slideUp 0.3s ease;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-close {
  position: absolute; top: 16px; right: 16px;
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border: none; background: rgba(0,0,0,0.04); border-radius: 50%;
  color: #6e6e73; cursor: pointer; transition: all 0.2s;
}
.modal-close:hover { background: rgba(0,0,0,0.08); color: #1d1d1f; }

.modal-title {
  font-size: 28px; font-weight: 700; letter-spacing: -0.025em;
  color: #1d1d1f; margin-bottom: 4px; text-align: center;
}
.modal-desc {
  font-size: 14px; color: #86868b; text-align: center; margin-bottom: 24px;
}
.modal-switch {
  color: #0071e3; text-decoration: none; font-weight: 500;
}
.modal-switch:hover { text-decoration: underline; }

/* Server error */
.modal-error {
  display: flex; align-items: center; gap: 8px;
  background: #fff2f0; border: 1px solid #ffccc7; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 16px;
  color: #ff3b30; font-size: 13px;
}
.modal-error-icon { flex-shrink: 0; }

/* Form */
.modal-form { display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label {
  font-size: 13px; font-weight: 600; color: #1d1d1f;
}

/* Input with icon */
.input-wrap { position: relative; display: flex; align-items: center; }
.form-input {
  width: 100%;
  padding: 12px 36px 12px 14px;
  border: 1.5px solid #d2d2d7;
  border-radius: 10px;
  font-size: 15px; font-family: inherit; color: #1d1d1f;
  background: #f5f5f7; transition: all 0.2s; outline: none;
}
.form-input:focus {
  border-color: #0071e3; background: #fff;
  box-shadow: 0 0 0 3px rgba(0,113,227,0.12);
}
.form-input::placeholder { color: #aeaeb2; }

/* Validation states */
.input-valid { border-color: #34c759; }
.input-valid:focus { border-color: #34c759; box-shadow: 0 0 0 3px rgba(52,199,89,0.12); }
.input-invalid { border-color: #ff3b30; }
.input-invalid:focus { border-color: #ff3b30; box-shadow: 0 0 0 3px rgba(255,59,48,0.12); }

.input-icon {
  position: absolute; right: 12px; font-size: 14px; font-weight: 700;
  pointer-events: none;
}
.input-icon-ok { color: #34c759; }
.input-icon-err { color: #ff3b30; }

/* Field hints */
.field-hint {
  font-size: 12px; color: #aeaeb2; margin: 0; padding-left: 2px;
}
.field-hint-err { color: #ff3b30; }
.field-hint-ok { color: #34c759; }

.form-submit {
  margin-top: 10px; padding: 13px; border: none; border-radius: 12px;
  background: #0071e3; color: #fff; font-family: inherit; font-size: 16px;
  font-weight: 600; cursor: pointer; transition: all 0.25s;
  box-shadow: 0 2px 12px rgba(0,113,227,0.25);
  display: flex; align-items: center; justify-content: center; min-height: 46px;
}
.form-submit:hover:not(:disabled) {
  background: #0066cc; box-shadow: 0 6px 24px rgba(0,113,227,0.35);
}
.form-submit:disabled { opacity: 0.6; cursor: not-allowed; }

.spinner {
  width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
