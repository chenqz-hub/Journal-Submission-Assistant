const translations = {
    'zh': {
        title: '科研投稿自动化排版 - SciAutoFormat',
        header_title: '科研投稿自动化排版助手 V1.0',
        header_desc: '输入期刊链接 + 上传Word / Markdown / TXT 原稿，一键完成格式重排、自动拆分与Cover Letter生成',
        access_code_label: '🔐 访问口令：',
        access_code_placeholder: '无口令可留空',
        sec1_title: '1. 期刊规则解析',
        sec1_rad1: '链接 URL',
        sec1_rad2: '文本粘贴 (推荐 - 最稳当)',
        sec1_rad3: 'PDF 上传',
        sec1_url_placeholder: '输入期刊《作者指南》链接',
        sec1_btn_url: '自动解析规则',
        sec1_txt_desc: '<strong>💡 为什么推荐？</strong> 相比 PDF 和 URL，直接粘贴文本能避开格式干扰和反爬限制，解析准确率最高。<br>请直接全选复制官网“Guidelines”页面的所有文字粘贴如下：',
        sec1_txt_placeholder: '请在此处粘贴《作者指南》的全文内容...',
        sec1_btn_txt: '粘贴文本解析',
        sec1_pdf_desc: '当期刊只提供 PDF 格式指南时使用。',
        sec1_btn_pdf: '上传 PDF 解析',
        sec2_title: '2. 论文智能排版与拆分（支持 Word / MD / TXT）',
        sec2_btn: '一键排版并生成打包文件',
        sec3_title: '3. 拒稿一键转投 (多文件合成新格式)',
        sec3_desc: '如果您被其他期刊拒稿，已有 <code>Title_Page.docx</code>、<code>Manuscript.docx</code> 等多个独立文件，可在此处<strong>同时选择并上传多个文件</strong>。<br>系统会洗去原本的格式，融合内容后，按照<strong>第1步中新期刊的规则</strong>重新生成格式并打包。',
        sec3_btn: '多文件合成转投打包',
        sec4_title: '4. Cover Letter 检查与修正',
        sec4_desc: '上传您现有的 Cover Letter 草稿（支持 Word / MD / TXT）。系统将根据<strong>第一步提取的期刊规则</strong>，自动把旧期刊名称替换为您指定的目标期刊，并为您<strong>智能增补遗漏的必填声明</strong>（如数据可用性、利益冲突等）。',
        sec4_placeholder: '[可选] 目标期刊名称（将被替换到信件中）',
        sec4_btn: '核查并修正 Cover Letter',
        sec5_title: '5. 单独表格格式转换 (Tables Formatting)',
        sec5_desc: '上传原稿（支持 Word / MD / TXT），提取文档中的所有表格，自动转换为三线表，单元格内容上下&左右居中，按照“一表一页”的格式规范生成独立文件，并保留上下文中的表头与注脚。',
        sec5_btn: '单独提取并排版表格',
        sec_res_title: '结果输出',
        sec_res_box: '等待操作...',
        sec_det_title: '二跳抓取明细',
        sec_det_th1: '页面',
        sec_det_th2: '命中规则数',
        sec_det_th3: '覆盖率',
        sec_det_th4: '命中字段'
    },
    'en': {
        title: 'AutoFormat Assistant - SciAutoFormat',
        header_title: 'SciAutoFormat Web Assistant V1.0',
        header_desc: 'Input Journal URL + Upload Word/MD/TXT draft. One-click formatting, splitting, and Cover Letter generation.',
        access_code_label: '🔐 Access Code:',
        access_code_placeholder: 'Optional',
        sec1_title: '1. Journal Guidelines Parsing',
        sec1_rad1: 'URL Link',
        sec1_rad2: 'Pasted Text (Recommended)',
        sec1_rad3: 'PDF Upload',
        sec1_url_placeholder: 'Input Journal "Author Guidelines" URL',
        sec1_btn_url: 'Parse Over URL',
        sec1_txt_desc: '<strong>💡 Why Recommended?</strong> Compared to PDF/URL, pasting text bypasses format issues & anti-bot checks.<br>Please select, copy and paste the entire "Author Guidelines" page here:',
        sec1_txt_placeholder: 'Paste the full "Author Guidelines" text here...',
        sec1_btn_txt: 'Parse Text',
        sec1_pdf_desc: 'Use this when the journal only provides guidelines in PDF format.',
        sec1_btn_pdf: 'Upload & Parse PDF',
        sec2_title: '2. Smart Formatting & Splitting (Word/MD/TXT)',
        sec2_btn: 'Format & Generate Zip',
        sec3_title: '3. One-Click Resubmission (Merge Multiple Files)',
        sec3_desc: 'If rejected and you have multiple files like <code>Title_Page.docx</code>, <code>Manuscript.docx</code>, you can <strong>upload them all at once</strong> here.<br>The system will strip old formats, merge contents, and re-format/split following the <strong>new journal rules parsed in Step 1</strong>.',
        sec3_btn: 'Merge & Format for Resubmission',
        sec4_title: '4. Cover Letter Check & Fix',
        sec4_desc: 'Upload your current Cover Letter draft (Word/MD/TXT). The system will strictly replace the old journal name with the target one, and <strong>smartly append missing mandatory declarations</strong> (e.g. Data Availability, Conflicts of Interest) based on <strong>Step 1</strong>.',
        sec4_placeholder: '[Optional] Target Journal Name (to replace old ones)',
        sec4_btn: 'Review & Fix Cover Letter',
        sec5_title: '5. Tables Formatting ONLY',
        sec5_desc: 'Upload your manuscript (Word/MD/TXT), we will extract all tables and convert them to academic three-line tables (all centered). Generated neatly as one table per page with surrounding captions kept.',
        sec5_btn: 'Extract & Format Tables',
        sec_res_title: 'Execution Results',
        sec_res_box: 'Waiting for operation...',
        sec_det_title: 'Crawl Detail History',
        sec_det_th1: 'Page URL',
        sec_det_th2: 'Rules Matched',
        sec_det_th3: 'Coverage',
        sec_det_th4: 'Hit Fields'
    }
};

let currentLang = localStorage.getItem('sa_lang') || 'zh'; // Default to Chinese

function updateLanguage(lang) {
    const texts = translations[lang];
    if (!texts) return;
    
    // Update elements with text/HTML content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (texts[key]) {
            el.innerHTML = texts[key];
        }
    });

    // Update elements with placeholder text
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (texts[key]) {
            el.setAttribute('placeholder', texts[key]);
        }
    });
}

function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('sa_lang', currentLang);
    updateLanguage(currentLang);
}

// Initial application
document.addEventListener("DOMContentLoaded", () => {
    updateLanguage(currentLang);
});
