<script setup>
import { inject } from 'vue'

const t = inject('t')
</script>

<template>
  <footer class="site-footer glass">
    <div class="container">
      <div class="footer-grid">
        <!-- Brand -->
        <div class="footer-col brand-col">
          <h4 class="footer-logo">VideoDown</h4>
          <p class="footer-desc">{{ t.footer_brand_desc }}</p>
          <p class="footer-updated">{{ t.footer_updated }}</p>
        </div>

        <!-- Quick Links -->
        <div class="footer-col">
          <h5 class="footer-heading">{{ t.footer_quick_links }}</h5>
          <ul class="footer-links">
            <li><a href="#">{{ t.footer_link_home }}</a></li>
            <li><a href="#features">{{ t.footer_link_features }}</a></li>
            <li><a href="#faq">{{ t.footer_link_faq }}</a></li>
            <li><a href="#how-to-use">{{ t.footer_link_howto }}</a></li>
          </ul>
        </div>

        <!-- Platforms -->
        <div class="footer-col">
          <h5 class="footer-heading">{{ t.footer_platforms_col }}</h5>
          <ul class="footer-links">
            <li><a href="#">{{ t.footer_link_youtube }}</a></li>
            <li><a href="#">{{ t.footer_link_bilibili }}</a></li>
            <li><a href="#">{{ t.footer_link_douyin }}</a></li>
          </ul>
        </div>

        <!-- About / Contact -->
        <div class="footer-col">
          <h5 class="footer-heading">{{ t.footer_contact }}</h5>
          <ul class="footer-links">
            <li><a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener noreferrer">{{ t.footer_powered }} yt-dlp</a></li>
            <li><span class="footer-muted">{{ t.footer_sites }}</span></li>
            <li><span class="footer-muted">{{ t.footer_no_account }}</span></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <p class="footer-copy">{{ t.footer_copy }}</p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: auto; padding: 72px 0 32px;
  border-top: 1px solid rgba(0,0,0,0.08);
  background: rgba(245, 245, 247, 0.6);
  backdrop-filter: saturate(180%) blur(16px);
  -webkit-backdrop-filter: saturate(180%) blur(16px);
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 40px;
}

.footer-logo {
  font-size: 18px; font-weight: 700; color: #1d1d1f;
  margin-bottom: 12px; letter-spacing: -0.022em;
}
.footer-desc {
  font-size: 13px; color: #86868b; line-height: 1.7; margin-bottom: 12px;
}
.footer-updated {
  font-size: 11px; color: #aeaeb2;
}

.footer-heading {
  font-size: 12px; font-weight: 600; color: #1d1d1f;
  text-transform: uppercase; letter-spacing: 0.04em;
  margin-bottom: 14px;
}

.footer-links { list-style: none; padding: 0; }
.footer-links li { margin-bottom: 8px; }
.footer-links a {
  font-size: 13px; color: #6e6e73; text-decoration: none;
  transition: color 0.2s;
}
.footer-links a:hover { color: #1d1d1f; }

.footer-muted {
  font-size: 13px; color: #86868b;
}

.footer-bottom {
  margin-top: 48px; padding-top: 24px;
  border-top: 1px solid rgba(0,0,0,0.06);
  text-align: center;
}
.footer-copy {
  font-size: 12px; color: #86868b;
}

/* ── Responsive ─────────────────────────────────── */
@media (max-width: 768px) {
  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: 32px;
  }
  .brand-col { grid-column: 1 / -1; }
}
@media (max-width: 480px) {
  .footer-grid { grid-template-columns: 1fr; gap: 28px; }
  .site-footer { padding: 48px 0 24px; }
}
</style>
