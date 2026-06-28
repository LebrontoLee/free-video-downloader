/**
 * Simple i18n system (Chinese / English) — no dependencies.
 */

export const messages = {
  zh: {
    // Nav
    nav_title: 'VideoDown',
    nav_pro: '升级到 Pro →',

    // Hero
    hero_title: '下载任何视频',
    hero_sub: '基于行业领先的 yt-dlp 引擎，支持 1,700+ 网站',
    hero_placeholder: '粘贴视频链接...',
    hero_trust_1: '无需注册',
    hero_trust_2: '免费无限下载',
    hero_trust_3: '无广告、无追踪',
    hero_examples: '试试示例：',

    // Video Preview
    preview_quality: '选择画质',
    preview_download: '下载视频',
    preview_downloading: '下载中...',
    preview_new_url: '新链接',
    merge_badge: '合成',

    // Progress
    progress_downloading: '下载中...',
    progress_processing: '处理中...',
    progress_complete: '下载完成！',
    progress_downloaded: '已下载',
    progress_speed: '速度',
    progress_eta: '剩余时间',
    progress_save_file: '保存文件',

    // File List
    files_title: '下载记录',
    files_empty: '暂无下载记录，粘贴链接开始下载吧！',

    // Pro Banner
    pro_badge: 'PRO',
    pro_title: '解锁全部功能',
    pro_desc: '获取无限优质下载体验，没有任何限制。',
    pro_feat_1: '4K / 8K 超高清下载',
    pro_feat_2: '批量下载多视频',
    pro_feat_3: '完整播放列表 & 频道支持',
    pro_feat_4: '内置格式转换器',
    pro_feat_5: '优先下载速度',
    pro_feat_6: '无广告体验',
    pro_price_before: '',
    pro_price: '$4.99',
    pro_period: ' / 月',
    pro_cta: '立即升级',
    pro_note: '即将上线 · 无需信用卡即可试用',

    // Footer
    footer_powered: '基于',
    footer_sites: '支持 1700+ 网站',
    footer_no_account: '无需账号',
    footer_copy: '© 2026 Free Video Downloader',

    // General
    error_network: '网络错误，请检查连接后重试。',
    error_extract: '无法解析视频信息',
    lang_switch: 'English',
    size_unknown: '大小未知',

    // AI Panel
    ai_back: '返回',
    ai_title: 'AI 视频分析',
    ai_loading_subtitles: '正在提取字幕...',
    ai_subtitle_error: '字幕提取失败',
    ai_go_back: '返回',
    ai_no_subtitles_title: '该视频暂无字幕',
    ai_no_subtitles_desc: 'AI 分析功能需要视频字幕或自动生成的字幕才能工作。请尝试其他有字幕的视频。',
    ai_tab_summary: 'AI 总结',
    ai_tab_mindmap: '思维导图',
    ai_tab_chat: 'AI 问答',
    ai_tab_subtitles: '字幕文本',

    // Summary
    ai_summary_desc: '基于视频字幕生成 AI 智能总结，快速了解视频核心内容。',
    ai_generate_summary: '生成 AI 总结',
    ai_generating: '正在生成总结...',
    ai_stop: '停止',
    ai_copy: '复制',
    ai_regenerate: '重新生成',
    ai_summary_error: '生成总结失败',

    // Mind Map
    ai_mindmap_desc: '基于视频内容自动生成结构化思维导图，帮助快速梳理知识结构。',
    ai_generate_mindmap: '生成思维导图',
    ai_generating_mindmap: '正在生成思维导图...',
    ai_mindmap_error: '生成思维导图失败',
    ai_mindmap_download_svg: '下载 SVG 矢量图',
    ai_mindmap_download_png: '下载 PNG 高清图',
    ai_mindmap_fullscreen: '全屏展示',
    ai_mindmap_exit_fullscreen: '退出全屏',
    ai_mindmap_fit: '适应屏幕',

    // Chat
    ai_chat_placeholder: '针对视频内容提问，AI 将基于字幕为你解答。',
    ai_chat_input: '针对视频内容提问...',
    ai_thinking: '思考中...',
    ai_clear_chat: '清除对话',
    ai_retry: '重试',
    ai_analyze: 'AI 分析',
    ai_metadata_notice: '该视频无字幕，AI 分析基于视频标题、简介和标签进行，结果可能不够精确。',

    // Subtitle Viewer
    sv_total: '共',
    sv_entries: '条字幕',
    sv_lang: '语言',
    sv_auto: '自动生成',
    sv_manual: '人工字幕',
    sv_search_placeholder: '搜索字幕...',
    sv_sort_desc: '倒序',
    sv_sort_asc: '正序',
    sv_copy: '复制',
    sv_download: '下载',
    sv_download_srt: '下载 SRT',
    sv_download_txt: '下载 TXT',
    sv_no_results: '无匹配结果',
    sv_empty: '暂无字幕',
    sv_showing: '显示',
  },

  en: {
    // Nav
    nav_title: 'VideoDown',
    nav_pro: 'Upgrade to Pro →',

    // Hero
    hero_title: 'Download Any Video, Anywhere.',
    hero_sub: 'Powered by industry-leading yt-dlp engine. Supports 1,700+ websites.',
    hero_placeholder: 'Paste your video URL here...',
    hero_trust_1: 'No registration required',
    hero_trust_2: 'Free & unlimited downloads',
    hero_trust_3: 'No ads, no trackers',
    hero_examples: 'Try an example:',

    // Video Preview
    preview_quality: 'Select Quality',
    preview_download: 'Download Video',
    preview_downloading: 'Downloading...',
    preview_new_url: 'New URL',
    merge_badge: 'merge',

    // Progress
    progress_downloading: 'Downloading...',
    progress_processing: 'Processing...',
    progress_complete: 'Download Complete!',
    progress_downloaded: 'Downloaded',
    progress_speed: 'Speed',
    progress_eta: 'ETA',
    progress_save_file: 'Save File',

    // File List
    files_title: 'Recent Downloads',
    files_empty: 'No downloads yet. Paste a URL to get started!',

    // Pro Banner
    pro_badge: 'PRO',
    pro_title: 'Unlock the Full Power',
    pro_desc: 'Get unlimited access to premium features and download videos without any limitations.',
    pro_feat_1: '4K / 8K ultra HD downloads',
    pro_feat_2: 'Batch download multiple videos',
    pro_feat_3: 'Full playlist & channel support',
    pro_feat_4: 'Built-in format converter',
    pro_feat_5: 'Priority download speed',
    pro_feat_6: 'Ad-free experience',
    pro_price_before: '',
    pro_price: '$4.99',
    pro_period: ' / month',
    pro_cta: 'Upgrade Now',
    pro_note: 'Coming soon · No credit card required to try',

    // Footer
    footer_powered: 'Powered by',
    footer_sites: 'Supports 1700+ websites',
    footer_no_account: 'No account required',
    footer_copy: '© 2026 Free Video Downloader',

    // General
    error_network: 'Network error. Please check your connection and try again.',
    error_extract: 'Failed to extract video info',
    lang_switch: '中文',
    size_unknown: 'Unknown',

    // AI Panel
    ai_back: 'Back',
    ai_title: 'AI Video Analysis',
    ai_loading_subtitles: 'Extracting subtitles...',
    ai_subtitle_error: 'Failed to extract subtitles',
    ai_go_back: 'Go Back',
    ai_no_subtitles_title: 'No Subtitles Available',
    ai_no_subtitles_desc: 'AI analysis requires subtitles or auto-generated captions. Please try a different video with subtitles.',
    ai_tab_summary: 'AI Summary',
    ai_tab_mindmap: 'Mind Map',
    ai_tab_chat: 'Ask AI',

    // Summary
    ai_summary_desc: 'Generate an AI-powered summary from video subtitles to quickly grasp the key content.',
    ai_generate_summary: 'Generate AI Summary',
    ai_generating: 'Generating summary...',
    ai_stop: 'Stop',
    ai_copy: 'Copy',
    ai_regenerate: 'Regenerate',
    ai_summary_error: 'Failed to generate summary',

    // Mind Map
    ai_mindmap_desc: 'Auto-generate a structured mind map from video content to quickly visualize the knowledge structure.',
    ai_generate_mindmap: 'Generate Mind Map',
    ai_generating_mindmap: 'Generating mind map...',
    ai_mindmap_error: 'Failed to generate mind map',
    ai_mindmap_download_svg: 'Download SVG',
    ai_mindmap_download_png: 'Download PNG',
    ai_mindmap_fullscreen: 'Fullscreen',
    ai_mindmap_exit_fullscreen: 'Exit Fullscreen',
    ai_mindmap_fit: 'Fit to Screen',

    // Chat
    ai_chat_placeholder: 'Ask questions about the video content. AI will answer based on the transcript.',
    ai_chat_input: 'Ask a question about this video...',
    ai_thinking: 'Thinking...',
    ai_clear_chat: 'Clear chat',
    ai_retry: 'Retry',
    ai_analyze: 'AI Analyze',
    ai_metadata_notice: 'No subtitles available. AI analysis is based on video title, description, and tags — results may be less precise.',

    // Subtitle Viewer
    sv_total: '',
    sv_entries: 'entries',
    sv_lang: 'Language',
    sv_auto: 'Auto-generated',
    sv_manual: 'Manual',
    sv_search_placeholder: 'Search subtitles...',
    sv_sort_desc: 'Newest first',
    sv_sort_asc: 'Oldest first',
    sv_copy: 'Copy',
    sv_download: 'Download',
    sv_download_srt: 'Download SRT',
    sv_download_txt: 'Download TXT',
    sv_no_results: 'No matching entries',
    sv_empty: 'No subtitles',
    sv_showing: 'Showing',
  },
}

export default messages
