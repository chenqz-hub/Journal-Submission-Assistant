
const originalFetch = window.fetch;
window.fetch = async function () {
    let [resource, config] = arguments;
    if(resource.includes('/api/v1/')) {
        if(config === undefined) { config = {}; }
        if(config.headers === undefined) { config.headers = {}; }
        const accessCode = document.getElementById('accessCode') ? document.getElementById('accessCode').value.trim() : '';
        config.headers['X-Access-Code'] = accessCode;
    }
    return await originalFetch(resource, config);
};

const API_BASE = "/api/v1";

const btnParse = document.getElementById("btnParse");
const btnParseText = document.getElementById("btnParseText");
const btnParsePdf = document.getElementById("btnParsePdf"); // Added
const btnFormat = document.getElementById("btnFormat");
const btnTransfer = document.getElementById("btnTransfer"); // Added for multi-file transfer
const btnCoverLetter = document.getElementById("btnCoverLetter");

const journalUrlInput = document.getElementById("journalUrl");
const guidelineTextInput = document.getElementById("guidelineText");
const guidelinePdfInput = document.getElementById("guidelinePdf"); // Added
const wordFileInput = document.getElementById("wordFile");
const transferFilesInput = document.getElementById("transferFiles"); // Added
const journalNameInput = document.getElementById("journalName");
const resultBox = document.getElementById("resultBox");
const detailPanel = document.getElementById("detailPanel");
const detailSummary = document.getElementById("detailSummary");
const attemptSummary = document.getElementById("attemptSummary");
const detailTableBody = document.getElementById("detailTableBody");

function hideDetailPanel() {
	detailPanel.style.display = "none";
	detailSummary.textContent = "";
	attemptSummary.innerHTML = "";
	detailTableBody.innerHTML = "";
}

function formatScore(value) {
	if (typeof value !== "number") return "-";
	return `${Math.round(value * 100)}%`;
}

function createRuleTags(fields) {
	if (!Array.isArray(fields) || fields.length === 0) {
		return "<span>-</span>";
	}
	return `<div class="rule-tags">${fields
		.map((field) => `<span class="rule-tag">${field}</span>`)
		.join("")}</div>`;
}

function renderTwoHopDetails(data) {
	const crawl = data?.data?.crawl;
	if (!crawl || !Array.isArray(crawl.pages) || crawl.pages.length === 0) {
		hideDetailPanel();
		return;
	}

	detailPanel.style.display = "block";
	detailSummary.textContent = `模式：${crawl.mode || "-"}；抓取页面：${crawl.pages.length} 个；子页面：${crawl.subpage_count || 0} 个`;

	const attempts = Array.isArray(crawl.main_attempts) ? crawl.main_attempts : [];
	if (attempts.length > 0) {
		const attemptItems = attempts
			.map((item) => {
				const url = item?.url || "";
				const status = item?.status ?? "-";
				const result = item?.result || "-";
				return `<li>${url}（status: ${status}，result: ${result}）</li>`;
			})
			.join("");

		attemptSummary.innerHTML = `<strong>候选链接尝试：</strong><ul>${attemptItems}</ul>`;
	} else {
		attemptSummary.innerHTML = "";
	}

	detailTableBody.innerHTML = crawl.pages
		.map((page) => {
			const url = page.url || "";
			const title = page.title || "未命名页面";
			const matchedCount = page.matched_rule_count ?? 0;
			const pageCoverage = formatScore(page.page_coverage_score);
			const fieldsHtml = createRuleTags(page.matched_rule_fields);
			return `
				<tr>
					<td><div><strong>${title}</strong></div><div><a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a></div></td>
					<td>${matchedCount}</td>
					<td>${pageCoverage}</td>
					<td>${fieldsHtml}</td>
				</tr>
			`;
		})
		.join("");
}

function renderParsedRules(data) {
    const rules = data?.data?.rules || {};
    const evidence = data?.data?.evidence?.wording_snippets || [];
    
    // Check if we actually found anything meaningful
    const keyFields = [
        "manuscript_word_limit", "abstract_word_limit", 
        "line_spacing", "font_family", "reference_style", 
        "figure_min_dpi", "figure_formats"
    ];
    
    const hasKeyRules = keyFields.some(k => 
        rules[k] !== null && rules[k] !== undefined && (Array.isArray(rules[k]) ? rules[k].length > 0 : true)
    );
    
    // If no key rules found, show specific warning state
    if (!hasKeyRules && (!rules.required_sections || rules.required_sections.length === 0)) {
         resultBox.innerHTML = `
            <div style="background-color:#fff3cd; border:1px solid #ffeeba; color:#856404; padding:15px; border-radius:5px;">
                <h4 style="margin-top:0; color:#856404;">⚠️ 未能提取到有效规则</h4>
                <p>虽然文件已上传，但系统未识别出任何排版要求。</p>
                <div style="margin:10px 0; font-size:0.9em;">
                    <strong>可能原因：</strong>
                    <ul style="margin:5px 0; padding-left:20px;">
                        <li>PDF 是<strong>扫描版/图片</strong>（非文字版），无法提取文本。</li>
                        <li>PDF 内容受加密保护或编码异常。</li>
                        <li>上传的文件可能不是完整的《作者指南》。</li>
                    </ul>
                </div>
                <div style="margin-top:15px; border-top:1px solid #ffeeba; padding-top:10px;">
                    <strong>建议方案：</strong><br>
                    请打开 PDF，手动复制关于“Manuscript Formatting”或“Preparation”章节的文本，<br>
                    切换到上方的 <b>“文本粘贴”</b> 模式进行解析。
                </div>
            </div>
         `;
         return;
    }

    // ... Standard Parsing Render ...
    const findEvidence = (val) => {
        if (!val) return null;
        return evidence.find(s => s.includes(val.toString()));
    };

    let html = `<div style="text-align:left; font-size: 14px; line-height: 1.4; font-family: sans-serif;">`;
    
    // --- 1. Success Section ---
    html += `<h4 style="margin: 0 0 8px 0; color:#2c3e50; border-bottom:2px solid #2ecc71; padding-bottom:4px;">✅ 成功解析的要素</h4>`;
    
      const getVal = (val) => {
          if (val === null || val === undefined) return '';
          if (typeof val === 'object') return val.value || JSON.stringify(val);
          return val;
      };

      // Word Limits
      if (rules.manuscript_word_limit) {
          const val = getVal(rules.manuscript_word_limit);
          const isNum = !isNaN(val);
          html += `<div style="margin-bottom:4px;"><strong>论文字数限制 (manuscript_word_limit)：</strong>${val}${isNum ? ' 字' : ''}</div>`;
          const ev = findEvidence(val);
        if (ev) html += `<div style="color:#666; font-size:0.9em; margin-left:1em; margin-bottom:4px; background:#f9f9f9; padding:2px 5px; border-left:3px solid #ddd;"><i>来源文本片段提到："${ev.substring(0, 150)}${ev.length > 150 ? '...' : ''}"</i></div>`;
    }
    if (rules.abstract_word_limit) {
          const val = getVal(rules.abstract_word_limit);
          const isNum = !isNaN(val);
          html += `<div style="margin-bottom:4px;"><strong>摘要字数限制 (abstract_word_limit)：</strong>${val}${isNum ? ' 字' : ''}</div>`;
          const ev = findEvidence(val);
        if (ev) html += `<div style="color:#666; font-size:0.9em; margin-left:1em; margin-bottom:4px; background:#f9f9f9; padding:2px 5px; border-left:3px solid #ddd;"><i>来源文本片段提到："${ev.substring(0, 150)}${ev.length > 150 ? '...' : ''}"</i></div>`;
    }
    
    // Basic Formatting
    if (rules.line_spacing) {
          const val = getVal(rules.line_spacing);
          html += `<div style="margin-bottom:4px;"><strong>行距 (line_spacing)：</strong>${val}</div>`;
          const ev = findEvidence(val);
        if (ev) html += `<div style="color:#666; font-size:0.9em; margin-left:1em; margin-bottom:4px; background:#f9f9f9; padding:2px 5px; border-left:3px solid #ddd;"><i>来源文本片段提到："${ev.substring(0, 150)}${ev.length > 150 ? '...' : ''}"</i></div>`;
    }
    if (rules.font_family) {
          const val = getVal(rules.font_family);
          html += `<div style="margin-bottom:4px;"><strong>字体 (font_family)：</strong>${val}</div>`;
          const ev = findEvidence(val);
        if (ev) html += `<div style="color:#666; font-size:0.9em; margin-left:1em; margin-bottom:4px; background:#f9f9f9; padding:2px 5px; border-left:3px solid #ddd;"><i>来源文本片段提到："${ev.substring(0, 150)}${ev.length > 150 ? '...' : ''}"</i></div>`;
    }

    // Images
    if ((rules.figure_formats && rules.figure_formats.length > 0) || rules.figure_min_dpi) {
        html += `<div style="margin-top: 8px; margin-bottom: 2px;"><strong>图片要求：</strong></div>
                 <ul style="margin:0 0 5px 20px;">`;
        if (rules.figure_formats && rules.figure_formats.length > 0) html += `<li>格式：${rules.figure_formats.join(", ")}</li>`;
        if (rules.figure_min_dpi) {
              const displayDpi = getVal(rules.figure_min_dpi);
              html += `<li>分辨率 (figure_min_dpi)：${displayDpi} DPI</li>`;
              const ev = findEvidence(displayDpi);
            if (ev) html += `<div style="color:#666; font-size:0.9em; margin-left:1em; margin-bottom:2px;"><i>来源文本片段提到："${ev.substring(0, 100)}..."</i></div>`;
        }
        html += `</ul>`;
    }

    // Declarations
    html += `<div style="margin-top: 8px; margin-bottom: 2px;"><strong>必需声明 (关键合规检查)：</strong></div>
             <ul style="margin:0 0 5px 20px;">`;
    
    // Function to add declaration item with evidence
    const addDecl = (label, val, keyword) => {
        let itemHtml = `<li>${label}：${val ? "<span style='color:green;font-weight:bold'>必须 (Yes)</span>" : "无明确要求"}</li>`; // Fixed label
        if (val) {
             let ev = null;
             // Try strict match first
             if (evidence && evidence.length > 0) {
                 ev = evidence.find(s => s.toLowerCase().includes(keyword.toLowerCase()));
             }
             
             if (ev) {
                // Highlight snippet
                const shortEv = ev.length > 200 ? ev.substring(0, 200) + "..." : ev;
                itemHtml += `<div style="color:#666; font-size:0.85em; margin-left:2px; margin-top:1px; background:#f5f5f5; padding:2px 4px; border-left:2px solid #ccc; font-style:italic;">来源文本片段提到："${shortEv}"</div>`;
             }
        }
        return itemHtml;
    };

    html += addDecl("投稿信 (Cover Letter)", rules.cover_letter_required, "Cover letter");
    html += addDecl("伦理声明 (Ethics Query)", rules.ethics_statement_required, "Ethics");
    html += addDecl("利益冲突声明 (Conflict of Interest)", rules.conflict_statement_required, "Conflict");
    if (rules.data_availability_required) html += addDecl("数据可用性声明 (Data Availability)", true, "Data availability"); 
    
    html += `</ul>`;

    // Structural Sections
    if (rules.required_sections && rules.required_sections.length > 0) {
        html += `<div style="margin-top: 8px; margin-bottom: 2px;"><strong>必需章节结构：</strong></div>
                 <ul style="margin:0; padding-left: 20px;">
                    ${rules.required_sections.map(s => `<li style="margin-bottom:0; line-height:1.4;">${s}</li>`).join("")}
                 </ul>`;
    }

    // --- 2. Warning Section ---
    const missing = [];
    if (!rules.reference_style) missing.push({name: "参考文献格式 (reference_style)", desc: "系统无法自动将引文调整为特定风格（如 APA/Vancouver）。建议您查看指南中关于 References 的具体示例。"});
    if (!rules.font_size_pt) missing.push({name: "正文字号 (font_size_pt)", desc: "系统可能会使用默认字号 12pt。"});
    if (!rules.title_length_limit) missing.push({name: "标题长度限制 (title_length_limit)", desc: ""});

    if (missing.length > 0) {
        html += `<h4 style="margin: 15px 0 8px 0; color:#e67e22; border-bottom:2px solid #f1c40f; padding-bottom:4px;">⚠️ 未解析到的要素 (需要在 Word 排版后留意)</h4>`;
        missing.forEach(m => {
            html += `<div style="margin-bottom:6px;">
                <div><strong>${m.name}：</strong><span style="color:#e74c3c">null (未识别)</span></div>
                ${m.desc ? `<div style="color:#666; font-size:0.9em; margin-left:1em;">影响：${m.desc}</div>` : ""}
            </div>`;
        });
    }
    
    html += `</div>`;
    resultBox.innerHTML = html;
}

function showResult(title, data) {
    if (data && data.data && data.data.rules) {
        // Use custom renderer for parse results
        renderParsedRules(data);
    } else if ((title === "文档排版成功" || title === "多文件转投打包成功") && data && data.data && data.data.download_url) {
        // Special renderer for format document success
        let warningHtml = "";
        if (data.data.dpi_warnings && data.data.dpi_warnings.length > 0) {
            warningHtml = `
                <div style="margin-top: 20px; padding: 15px; border-left: 5px solid #e74c3c; background-color: #fdf5f5; text-align: left;">
                    <h4 style="color: #c0392b; margin-top: 0;">⚠️ 图片格式/DPI 警告：</h4>
                    <ul style="color: #e74c3c; font-size: 0.9em; margin-bottom: 0; padding-left: 20px;">
                        ${data.data.dpi_warnings.map(w => `<li style="margin-bottom: 5px;"><strong>${w.document} - ${w.image_name}</strong>: 检测到 ${w.dpi} DPI (尺寸 ${w.dimensions})。<br/><span style="color:#7f8c8d;">${w.suggestion}</span></li>`).join("")}
                    </ul>
                </div>
            `;
        }
        
        resultBox.innerHTML = `
            <div style="text-align:center; padding: 20px;">
                <h3 style="color:#27ae60; margin-top:0;">🎉 ${title}</h3>
                <p>${data.message || "您的文档已按照期刊规则完成排版！"}</p>
                <div style="margin: 20px 0;">
                    <a href="${data.data.download_url}" target="_blank" download style="background-color: #e67e22; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        📦 点击下载投稿文档合集 (Zip)
                    </a>
                </div>
                <p style="color:#7f8c8d; font-size: 0.9em;">文件已保存在服务器：<code>${data.data.filename}</code></p>
                ${warningHtml}
            </div>
        `;
    } else if (title === "Cover Letter 生成成功" || title === "Cover Letter 核对与修正完成（本地处理）") {
        if (data && data.data && data.data.cover_letter) {
            let downloadBtn = "";
            if (data.data.download_url) {
                downloadBtn = `
                <div style="margin: 15px 0;">
                    <a href="${data.data.download_url}" target="_blank" download style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        📥 下载修正后的 Cover Letter (Word)
                    </a>
                </div>`;
            }
        
             resultBox.innerHTML = `
                <div>
                    <h3 style="color:#27ae60; margin-top:0;">🎉 Cover Letter 核查与修正完成</h3>
                    <p>系统已根据期刊规则帮您补齐了相关声明，并替换了期刊名称。</p>
                    ${downloadBtn}
                    <textarea style="width:100%; height:300px; padding:10px; border:1px solid #ccc; border-radius:4px; font-family:inherit; resize:vertical; margin-top: 10px;">${data.data.cover_letter}</textarea>
                </div>
            `;
        }
    } else {
        // Fallback for other results
	    resultBox.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
    }
}

function showError(error) {
	hideDetailPanel();
	const message = error?.message || "发生未知错误";
	resultBox.textContent = `请求失败\n\n${message}`;
}

async function ensureOk(response) {
	if (response.ok) {
		return;
	}

	let detail = "";
	try {
		const errorBody = await response.json();
		detail = errorBody?.detail ? `\n${errorBody.detail}` : "";
	} catch (error) {
		detail = "";
	}

	throw new Error(`HTTP ${response.status}${detail}`);
}

let lastParsedRules = null; // Store parsed rules

btnParse.addEventListener("click", async () => {
	const url = journalUrlInput.value.trim();
	if (!url) {
		resultBox.textContent = "请先输入期刊作者指南链接。";
		return;
	}

	resultBox.textContent = "正在解析期刊规则...";

	try {
		const response = await fetch(`${API_BASE}/parse-rules`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ url })
		});
		await ensureOk(response);

		const data = await response.json();
		lastParsedRules = data.data; // Save rules
		showResult("期刊规则解析成功", data);
		renderTwoHopDetails(data);
	} catch (error) {
		showError(error);
	}
});

btnParseText.addEventListener("click", async () => {
	const text = guidelineTextInput.value.trim();
	const sourceUrl = journalUrlInput.value.trim();

	if (!text) {
		resultBox.textContent = "请先粘贴作者指南文本。";
		return;
	}

	resultBox.textContent = "正在解析粘贴文本...";

	try {
		const response = await fetch(`${API_BASE}/parse-rules-text`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ text, source_url: sourceUrl || null })
		});
		await ensureOk(response);

		const data = await response.json();
		lastParsedRules = data.data; // Save rules
		showResult("粘贴文本解析成功", data);
		renderTwoHopDetails(data);
	} catch (error) {
		showError(error);
	}
});

// PDF Parsing Handler
if (btnParsePdf) {
    btnParsePdf.addEventListener("click", async () => {
        const file = guidelinePdfInput.files[0];
        if (!file) {
            resultBox.textContent = "请先选择 PDF 文件。";
            return;
        }
        
        resultBox.textContent = "正在解析 PDF 指南...";
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${API_BASE}/parse-rules-pdf`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Check if data is empty or suspiciously sparse
            const rules = data.data?.rules || {};
            const evidence = data.data?.evidence?.wording_snippets || [];
            if (!rules.manuscript_word_limit && !rules.reference_style && evidence.length === 0) {
                 resultBox.innerHTML = `<div style="color:#d35400; padding:10px; border:1px solid #f39c12; background:#fef9e7;">
                    <h4>⚠️ PDF 解析结果可能不完整</h4>
                    <p>未能从 PDF 中提取到足够的有效规则信息。</p>
                    <p><strong>可能原因：</strong></p>
                    <ul>
                        <li>该 PDF 可能是<strong>扫描件（图片格式）</strong>，导致无法提取文本内容。</li>
                        <li>该 PDF 内容较短，未包含完整的作者指南章节。</li>
                    </ul>
                    <p><strong>建议：</strong>请尝试手动复制 PDF 中的文本，使用上方的 <b>“文本粘贴”</b> 模式进行解析。</p>
                 </div>`;
                 // Still show partial results below if any
                 setTimeout(() => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = "<hr style='margin:20px 0; border:0; border-top:1px dashed #ccc;'/>";
                    resultBox.appendChild(tempDiv);
                    
                    const resultDiv = document.createElement('div');
                    renderParsedRules(data); // This renders into resultBox directly, clearing it. Need to fix renderParsedRules to append or return string.
                 }, 100);
                 // Actually renderParsedRules clears content. Let's just use renderParsedRules but prepend warning if needed.
            }
            
            lastParsedRules = data.data; 
            showResult("PDF 指南解析成功", data);
            
            // Post-check for warning
            if (!rules.manuscript_word_limit && !rules.reference_style && evidence.length === 0) {
                 const warningParams = `
                    <div style="margin-bottom:15px; color:#d35400; padding:10px; border:1px solid #f39c12; background:#fef9e7; border-radius:4px;">
                        <h4 style="margin-top:0;">⚠️ PDF 解析警告</h4>
                        <p style="margin-bottom:5px;">未能提取到关键规则。该 PDF 可能是<strong>扫描版/图片</strong>，或者内容不完整。</p>
                        <p style="margin-bottom:0;"><small>建议：请尝试手动复制文本，使用“文本粘贴”模式。</small></p>
                    </div>
                 `;
                 resultBox.innerHTML = warningParams + resultBox.innerHTML;
            }

            hideDetailPanel();
        } catch (error) {
            resultBox.textContent = `解析失败: ${error.message}`;
        }
    });
}

// Toggle Mode Handler
function toggleParseMode(event) {
    let mode;
    if (event && event.target) {
         mode = event.target.value;
    } else {
        // Fallback or init
        const checked = document.querySelector('input[name="parseMode"]:checked');
        if (checked) mode = checked.value;
    }
    
    if (!mode) return;

    // Fix IDs if they mismatch HTML
    // HTML has: id="modeUrl", "modeText", "modePdf"
    // Values are: "url", "text", "pdf"
    
    document.getElementById("modeUrl").style.display = (mode === "url") ? "block" : "none";
    document.getElementById("modeText").style.display = (mode === "text") ? "block" : "none";
    document.getElementById("modePdf").style.display = (mode === "pdf") ? "block" : "none";

    // Clear result box when switching modes to avoid confusion
    if (resultBox) resultBox.textContent = "等待操作...";
}

// Init
document.addEventListener("DOMContentLoaded", () => {
    const radios = document.querySelectorAll('input[name="parseMode"]');
    radios.forEach(r => r.addEventListener("change", toggleParseMode));
    
    // Trigger once
    toggleParseMode();
});

btnFormat.addEventListener("click", async () => {
	const url = journalUrlInput.value.trim();
	const file = wordFileInput.files[0];

	if (!file) {
		resultBox.textContent = "请先选择一个文档原稿（支持 .docx, .doc, .md, .txt）。";
		return;
	}

	if (!url && !lastParsedRules) {
		resultBox.textContent = "请先解析期刊规则（链接/文本/PDF）。";
		return;
	}

	resultBox.textContent = "正在上传并排版文档...";

	try {
		const formData = new FormData();
		formData.append("file", file);
		if (url) formData.append("journal_url", url);
        if (lastParsedRules) formData.append("parsed_rules", JSON.stringify(lastParsedRules));

		const response = await fetch(`${API_BASE}/format-document`, {
			method: "POST",
			body: formData
		});
		await ensureOk(response);

		const data = await response.json();
		showResult("文档排版成功", data);
		hideDetailPanel();
	} catch (error) {
		showError(error);
	}
});

btnTransfer.addEventListener("click", async () => {
	const url = journalUrlInput.value.trim();
	const files = transferFilesInput.files;

	if (!files || files.length === 0) {
		resultBox.textContent = "请先选择多个文件（如 Title_Page.docx, Manuscript.docx 等）。";
		return;
	}

	if (!url && !lastParsedRules) {
		resultBox.textContent = "请先解析 新期刊 的规则（链接/文本/PDF）。";
		return;
	}

	resultBox.textContent = `正在上传并合并 ${files.length} 个文件...`;

	try {
		const formData = new FormData();
		for (let i = 0; i < files.length; i++) {
			formData.append("files", files[i]);
		}
		if (url) formData.append("journal_url", url);
        if (lastParsedRules) formData.append("parsed_rules", JSON.stringify(lastParsedRules));

		const response = await fetch(`${API_BASE}/transfer-document`, {
			method: "POST",
			body: formData
		});
		await ensureOk(response);

		const data = await response.json();
		showResult("多文件转投打包成功", data);
		hideDetailPanel();
	} catch (error) {
		showError(error);
	}
});

btnCoverLetter.addEventListener("click", async () => {
    const journalName = journalNameInput.value.trim();
    // Use the file input specifically added for cover letter
    const cvFileInput = document.getElementById("coverLetterFile");
    const file = cvFileInput.files[0];

    if (!file) {
        resultBox.textContent = "请先上传您原版的 Cover Letter 草稿文件（支持 .docx, .doc, .md, .txt）。";
        return;
    }

    resultBox.textContent = "正在根据期刊规则核对并修正您的 Cover Letter...\n这可能需要十几秒钟的时间，请稍候。";

    try {
        const formData = new FormData();
        formData.append("file", file);
        if (journalName) formData.append("journal_name", journalName);
        if (lastParsedRules) formData.append("parsed_rules", JSON.stringify(lastParsedRules));

        const response = await fetch(`${API_BASE}/generate-cover-letter`, {
            method: "POST",
            body: formData
        });
        await ensureOk(response);

        const data = await response.json();
        showResult("Cover Letter 生成成功", data);
        hideDetailPanel();
    } catch (error) {
        showError(error);
    }
});






// ======= Table Only Format =======
const btnTableOnly = document.getElementById('btnTableOnly');
const tableOnlyFile = document.getElementById('tableOnlyFile');

if (btnTableOnly) {
    btnTableOnly.addEventListener('click', async () => {
        if (!tableOnlyFile.files || tableOnlyFile.files.length === 0) {
            alert('请上传需要提取和排版表格的 Word 文档');
            return;
        }

        const formData = new FormData();
        formData.append('file', tableOnlyFile.files[0]);

        const resultBox = document.getElementById('resultBox');
        resultBox.style.display = 'block';
        resultBox.innerHTML = '正在处理独立表格格式，请稍候...';

        try {
            const res = await fetch('/api/v1/format-tables-only', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (data.status === 'success') {
                resultBox.innerHTML = `<div class="success-msg">
                    ✅ 表格格式转换完成！<br>
                    <a href="${data.data.download_url}" target="_blank" download>点击下载单独的格式化表格文档 (.docx)</a>
                </div>`;
            } else {
                resultBox.innerHTML = `<div class="error-msg">❌ 失败：${data.message}</div>`;
            }
        } catch (e) {
            resultBox.innerHTML = `<div class="error-msg">❌ 请求出错：${e}</div>`;
        }
    });
}
