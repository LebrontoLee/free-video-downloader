<script setup>
import { ref, inject, onMounted, onBeforeUnmount } from 'vue'

const t = inject('t')
const lang = inject('lang')
const user = inject('user')
const isPro = inject('isPro')
const openAuthModal = inject('openAuthModal')
const handleLogout = inject('handleLogout')
const handleUpgrade = inject('handleUpgrade')

const showMenu = ref(false)
const userArea = ref(null)
let closeTimer = null

defineEmits(['reset', 'toggleLang'])

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function closeMenu() {
  showMenu.value = false
}

// Delay-close on mouse leave (gives user time to move to dropdown)
function onMouseLeave() {
  closeTimer = setTimeout(() => {
    showMenu.value = false
  }, 200)
}

function onMouseEnter() {
  if (closeTimer) {
    clearTimeout(closeTimer)
    closeTimer = null
  }
}

// Click outside to close
function onClickOutside(e) {
  if (userArea.value && !userArea.value.contains(e.target)) {
    showMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
  if (closeTimer) clearTimeout(closeTimer)
})

function onLogout() {
  closeMenu()
  handleLogout()
}

function onUpgradeOrManage() {
  closeMenu()
  handleUpgrade()
}
</script>

<template>
  <nav class="navbar" :class="{ 'navbar-pro': isPro }">
    <div class="nav-inner">
      <a href="#" class="nav-logo" @click.prevent="$emit('reset')">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" width="22" height="22">
          <path d="M21 7.5L12 2.25L3 7.5V16.5L12 21.75L21 16.5V7.5Z" fill="currentColor" opacity="0.15"/>
          <path d="M12 2.25L3 7.5V16.5L12 21.75L21 16.5V7.5L12 2.25Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M12 9.75L16.5 7.5L12 5.25L7.5 7.5L12 9.75Z" fill="currentColor"/>
          <path d="M12 9.75V16.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span class="nav-title">{{ t.nav_title }}</span>
      </a>
      <div class="nav-right">
        <button class="lang-btn" @click="$emit('toggleLang')" :title="t.lang_switch">
          {{ t.lang_switch }}
        </button>

        <!-- Not logged in -->
        <button v-if="!user" class="nav-signin-btn" @click="openAuthModal()">
          {{ t.account_sign_in }}
        </button>
        <a v-if="!user" href="#" class="nav-pro" @click.prevent="openAuthModal()">
          {{ t.nav_pro }}
        </a>

        <!-- Logged in -->
        <div v-if="user" ref="userArea" class="nav-user-area" @mouseleave="onMouseLeave" @mouseenter="onMouseEnter">
          <button class="nav-user-btn" @click="toggleMenu">
            <span class="nav-user-email">{{ user.email.split('@')[0] }}</span>
            <span v-if="isPro" class="nav-pro-badge">PRO</span>
            <svg class="nav-chevron" :class="{ open: showMenu }" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
              <path d="M4.22 6.22a.75.75 0 011.06 0L8 8.94l2.72-2.72a.75.75 0 111.06 1.06l-3.25 3.25a.75.75 0 01-1.06 0L4.22 7.28a.75.75 0 010-1.06z"/>
            </svg>
          </button>

          <div v-if="showMenu" class="nav-dropdown" @click.stop>
            <div class="nav-dropdown-header">
              <span class="nav-dropdown-email">{{ user.email }}</span>
              <span v-if="isPro" class="nav-pro-badge-dropdown">PRO 会员</span>
              <span v-else class="nav-pro-badge-dropdown-free">免费用户</span>
            </div>
            <button v-if="!isPro" class="nav-dropdown-item nav-dropdown-upgrade" @click="onUpgradeOrManage">
              {{ t.account_upgrade }}
            </button>
            <button v-if="isPro" class="nav-dropdown-item" @click="onUpgradeOrManage">
              {{ t.account_manage_sub }}
            </button>
            <button class="nav-dropdown-item nav-dropdown-logout" @click="onLogout">
              {{ t.account_logout }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 48px;
  background: rgba(245, 245, 247, 0.72);
  backdrop-filter: saturate(180%) blur(24px);
  -webkit-backdrop-filter: saturate(180%) blur(24px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
/* PRO user: premium navbar with gradient glow */
.navbar-pro {
  background: linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(240,245,255,0.88) 100%);
  border-bottom: 1px solid rgba(0, 113, 227, 0.15);
  box-shadow: 0 1px 12px rgba(0, 113, 227, 0.08);
}
.navbar-pro .nav-logo { color: #0059b3; }
.navbar-pro .logo-icon { color: #0071e3; }
.nav-inner {
  max-width: 1020px; margin: 0 auto; padding: 0 24px;
  height: 100%; display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { display: flex; align-items: center; gap: 8px; color: #1d1d1f; font-size: 17px; font-weight: 600; letter-spacing: -0.022em; text-decoration: none; transition: opacity 0.2s; }
.nav-logo:hover { opacity: 0.7; }
.logo-icon { color: #0071e3; }
.nav-right { display: flex; align-items: center; gap: 10px; }
.lang-btn {
  font-size: 12px; font-weight: 500; color: #6e6e73;
  background: rgba(0,0,0,0.04); border: 1px solid #d2d2d7; border-radius: 9999px;
  padding: 4px 10px; cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.lang-btn:hover { background: rgba(0,0,0,0.08); color: #1d1d1f; }
.nav-signin-btn {
  font-size: 13px; font-weight: 500; color: #1d1d1f;
  background: rgba(0,0,0,0.04); border: none; border-radius: 9999px;
  padding: 5px 14px; cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.nav-signin-btn:hover { background: rgba(0,0,0,0.08); }
.nav-pro { font-size: 13px; font-weight: 500; color: #0071e3; text-decoration: none; padding: 4px 12px; border-radius: 9999px; transition: background 0.2s; }
.nav-pro:hover { background: rgba(0, 113, 227, 0.08); }

/* -- Logged in -- */
.nav-user-area { position: relative; }
.nav-user-btn {
  display: flex; align-items: center; gap: 6px;
  background: none; border: 1px solid rgba(0,0,0,0.1); border-radius: 9999px;
  padding: 4px 4px 4px 12px; cursor: pointer; font-family: inherit;
  transition: all 0.2s;
}
.nav-user-btn:hover { background: rgba(0,0,0,0.04); }
.nav-user-email { font-size: 13px; font-weight: 500; color: #1d1d1f; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-pro-badge {
  font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
  background: linear-gradient(135deg, #f5c542, #e6a817); color: #1d1d1f;
  padding: 2px 8px; border-radius: 9999px; box-shadow: 0 1px 4px rgba(245,197,66,0.3);
}
.nav-chevron { color: #6e6e73; transition: transform 0.2s; }
.nav-chevron.open { transform: rotate(180deg); }

.nav-dropdown {
  position: absolute; top: calc(100% + 6px); right: 0;
  background: #fff; border-radius: 14px; padding: 8px; min-width: 220px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.05);
  animation: dropdownIn 0.15s ease;
}
@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.nav-dropdown-header {
  padding: 10px 12px 8px; border-bottom: 1px solid rgba(0,0,0,0.06); margin-bottom: 4px;
}
.nav-dropdown-email { font-size: 13px; color: #6e6e73; }
.nav-pro-badge-dropdown {
  display: inline-block; margin-top: 4px; font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
  background: #0071e3; color: #fff; padding: 2px 8px; border-radius: 9999px;
}
.nav-pro-badge-dropdown-free {
  display: inline-block; margin-top: 4px; font-size: 10px; font-weight: 500; letter-spacing: 0.04em;
  background: rgba(0,0,0,0.06); color: #6e6e73; padding: 2px 8px; border-radius: 9999px;
}
.nav-dropdown-item {
  display: block; width: 100%; text-align: left; padding: 10px 12px;
  background: none; border: none; border-radius: 8px;
  font-family: inherit; font-size: 14px; color: #1d1d1f; cursor: pointer;
  transition: background 0.15s;
}
.nav-dropdown-item:hover { background: rgba(0,0,0,0.04); }
.nav-dropdown-upgrade { color: #0071e3; font-weight: 600; }
.nav-dropdown-logout { color: #ff3b30; }
</style>
