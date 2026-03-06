import re
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will write a new static/index.html that includes the data-i18n tags and a language toggler.
new_html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="title">科研投稿自动化排版 - SciAutoFormat</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 data-i18n="header_title">科研投稿自动化排版助手 V1.0</h1>
                <button id="langToggle" onclick="toggleLanguage()" style="padding: 5px 10px; cursor: pointer; border: 1px solid #ccc; background: #fff; border-radius: 4px;">English / 中文</button>
            </div>
            <p data-i18n="header_desc">输入期刊链接 + 上传Word / Markdown / TXT 原稿，一键完成格式重排、自动拆分与Cover Letter生成</p>
            <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; gap: 10px;">
                <label for="accessCode" style="font-weight: bold; color: #856404; font-size: 14px;" data-i18n="access_code_label">🔐 访问口令：</label>
                <input type="password" id="accessCode" data-i18n-placeholder="access_code_placeholder" placeholder="无口令可留空" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 150px; font-size: 14px;">
            </div>
        </header>

        <main>
            <section class="card">
                <h2 data-i18n="sec1_title">1. 期刊规则解析</h2>
                <div style="margin-bottom: 10px; display: flex; gap: 15px;">
                    <label style="cursor: pointer;"><input type="radio" name="parseMode" value="url" checked> <span data-i18n="sec1_rad1">链接 URL</span></label>
                    <label style="cursor: pointer; font-weight:bold; color:#2c3e50;"><input type="radio" name="parseMode" value="text"> <span data-i18n="sec1_rad2">文本粘贴 (推荐 - 最稳当)</span></label>
                    <label style="cursor: pointer;"><input type="radio" name="parseMode" value="pdf"> <span data-i18n="sec1_rad3">PDF 上传</span></label>
                </div>

                <div id="modeUrl">
                    <input type="text" id="journalUrl" data-i18n-placeholder="sec1_url_placeholder" placeholder="输入期刊《作者指南》链接">
                    <button id="btnParse" data-i18n="sec1_btn_url">自动解析规则</button>
                </div>

                <div id="modeText" style="display:none">
                    <div style="margin-bottom:8px; color:#27ae60; font-size:0.9em; background:#f0fbf4; padding:5px 10px; border-radius:4px; border-left:3px solid #27ae60;" data-i18n="sec1_txt_desc">
                        <strong>💡 为什么推荐？</strong> 相比 PDF 和 URL，直接粘贴文本能避开格式干扰和反爬限制，解析准确率最高。<br>请直接全选复制官网“Guidelines”页面的所有文字粘贴如下：
                    </div>
                    <textarea id="guidelineText" rows="10" data-i18n-placeholder="sec1_txt_placeholder" placeholder="请在此处粘贴《作者指南》的全文内容..."></textarea>
                    <button id="btnParseText" data-i18n="sec1_btn_txt">粘贴文本解析</button>
                </div>

                <div id="modePdf" style="display:none">
                    <div style="margin-bottom:10px; color:#666; font-size:0.9em;" data-i18n="sec1_pdf_desc">当期刊只提供 PDF 格式指南时使用。</div>
                    <input type="file" id="guidelinePdf" accept=".pdf" style="margin-bottom:10px;">
                    <button id="btnParsePdf" data-i18n="sec1_btn_pdf">上传 PDF 解析</button>
                </div>
            </section>

            <section class="card">
                <h2 data-i18n="sec2_title">2. 论文智能排版与拆分（支持 Word / MD / TXT）</h2>
                <input type="file" id="wordFile" accept=".doc, .docx, .md, .txt">
                <button id="btnFormat" data-i18n="sec2_btn">一键排版并生成打包文件</button>
            </section>

            <section class="card">
                <h2 data-i18n="sec3_title">3. 拒稿一键转投 (多文件合成新格式)</h2>
                <div style="margin-bottom: 10px; color: #666; font-size: 0.9em;" data-i18n="sec3_desc">
                    如果您被其他期刊拒稿，已有 <code>Title_Page.docx</code>、<code>Manuscript.docx</code> 等多个独立文件，可在此处<strong>同时选择并上传多个文件</strong>。<br>系统会洗去原本的格式，融合内容后，按照<strong>第1步中新期刊的规则</strong>重新生成格式并打包。
                </div>
                <input type="file" id="transferFiles" accept=".doc, .docx, .md, .txt" multiple>
                <div style="margin-top: 10px;">
                    <button id="btnTransfer" data-i18n="sec3_btn">多文件合成转投打包</button>
                </div>
            </section>

            <section class="card">
                <h2 data-i18n="sec4_title">4. Cover Letter 检查与修正</h2>
                <div style="margin-bottom: 10px; color: #666; font-size: 0.9em;" data-i18n="sec4_desc">
                    上传您现有的 Cover Letter 草稿（支持 Word / MD / TXT）。系统将根据<strong>第一步提取的期刊规则</strong>，自动把旧期刊名称替换为您指定的目标期刊，并为您<strong>智能增补遗漏的必填声明</strong>（如数据可用性、利益冲突等）。
                </div>
                <input type="file" id="coverLetterFile" accept=".doc, .docx, .md, .txt" style="margin-bottom: 10px;"><br>
                <input type="text" id="journalName" data-i18n-placeholder="sec4_placeholder" placeholder="[可选] 目标期刊名称（将被替换到信件中）" style="width: 80%; max-width: 400px; margin-bottom: 10px;"><br>
                <button id="btnCoverLetter" data-i18n="sec4_btn">核查并修正 Cover Letter</button>
            </section>

            <section class="card">
                <h2 data-i18n="sec5_title">5. 单独表格格式转换 (Tables Formatting)</h2>
                <div style="margin-bottom:10px; color:#666; font-size:0.9em;" data-i18n="sec5_desc">
                    上传原稿（支持 Word / MD / TXT），提取文档中的所有表格，自动转换为三线表，单元格内容上下&左右居中，按照“一表一页”的格式规范生成独立文件，并保留上下文中的表头与注脚。
                </div>
                <input type="file" id="tableOnlyFile" accept=".doc, .docx, .md, .txt"><br>
                <button id="btnTableOnly" style="margin-top:10px;" data-i18n="sec5_btn">单独提取并排版表格</button>
            </section>

            <section class="card">
                <h2 data-i18n="sec_res_title">结果输出</h2>
                <div id="resultBox" class="result-box" data-i18n="sec_res_box">等待操作...</div>
            </section>

            <section class="card" id="detailPanel" style="display: none;">
                <h2 data-i18n="sec_det_title">二跳抓取明细</h2>
                <div id="detailSummary" class="detail-summary"></div>
                <div id="attemptSummary" class="attempt-summary"></div>
                <div class="table-wrap">
                    <table class="detail-table">
                        <thead>
                            <tr>
                                <th data-i18n="sec_det_th1">页面</th>
                                <th data-i18n="sec_det_th2">命中规则数</th>
                                <th data-i18n="sec_det_th3">覆盖率</th>
                                <th data-i18n="sec_det_th4">命中字段</th>
                            </tr>
                        </thead>
                        <tbody id="detailTableBody"></tbody>
                    </table>
                </div>
            </section>
        </main>
    </div>
    <script src="/static/js/i18n.js"></script>
    <script src="/static/js/app.js?v=2.6.1"></script>
</body>
</html>'''

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
