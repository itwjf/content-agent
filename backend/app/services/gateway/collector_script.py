"""
浏览器端采集脚本模板（SubTask 7.1）
通用型弹幕采集脚本：MutationObserver 监听评论区新增节点，脱敏后批量回传网关。
通过 GET /api/v1/gateway/browser/collector.js 动态下发，占位符由后端按查询参数替换。
DOM 选择器因平台改版而异，脚本提供 CONFIG.itemSelector/textSelector 供使用者按需覆盖。
"""

COLLECTOR_JS_TEMPLATE = r"""// ContentAgent 浏览器弹幕采集脚本 v1.0
// 用法：Tampermonkey 新建脚本粘贴本内容（或直接粘贴到直播间页面控制台执行）
// 风险提示：浏览器采集非官方授权方式，可能违反平台条款并触发风控，详见 docs/platform-access.md
(function () {
  'use strict';
  if (window.__CA_COLLECTOR__) { console.warn('[CA采集] 已注入，跳过'); return; }
  window.__CA_COLLECTOR__ = true;

  // ===== 配置（由后端按查询参数注入；可手动修改） =====
  var CONFIG = {
    server: __CA_SERVER__,            // 后端地址
    sessionId: __CA_SESSION_ID__,     // 直播场次ID
    token: __CA_TOKEN__,              // 回传令牌（后端未配置则为空串）
    itemSelector: '',                 // 弹幕条目选择器（可选，平台改版时手动指定，如 '.webcast-chatroom___item'）
    textSelector: '',                 // 条目内文本选择器（可选，默认取 innerText）
    flushInterval: 2000,              // 回传间隔(ms)
    maxBatch: 20,                     // 单批最大条数
    debug: true
  };

  var seen = new Set();   // 去重
  var pending = [];       // 待回传缓冲

  function log() { if (CONFIG.debug) console.log.apply(console, ['[CA采集]'].concat([].slice.call(arguments))); }

  // 用户名脱敏：DJB2 哈希，不回传原始昵称
  function maskUser(name) {
    if (!name) return null;
    var h = 5381;
    for (var i = 0; i < name.length; i++) h = ((h << 5) + h + name.charCodeAt(i)) >>> 0;
    return 'u' + h.toString(16);
  }

  // 从新增 DOM 节点提取 {user, content}
  function extract(node) {
    var items = [];
    if (node.nodeType !== 1) return items;
    var targets = [];
    if (CONFIG.itemSelector) {
      if (node.matches && node.matches(CONFIG.itemSelector)) targets.push(node);
      targets = targets.concat([].slice.call(node.querySelectorAll(CONFIG.itemSelector)));
    } else {
      targets = [node];
    }
    targets.forEach(function (el) {
      var text = (CONFIG.textSelector && el.querySelector(CONFIG.textSelector)
        ? el.querySelector(CONFIG.textSelector).innerText
        : el.innerText) || '';
      text = text.replace(/\s+/g, ' ').trim();
      if (!text || text.length > 200) return;
      // 常见结构："昵称：内容" / "昵称:内容"，否则整行视为内容
      var m = text.match(/^([^:：]{1,30})[:：]\s*(.+)$/);
      var user = m ? m[1] : null;
      var content = m ? m[2] : text;
      // 过滤系统提示类文案
      if (/^(欢迎|来了|关注了|加入了|点赞了|分享了)/.test(content)) return;
      items.push({ user: user, content: content });
    });
    return items;
  }

  function queue(item) {
    var key = (item.user || '') + '|' + item.content;
    if (seen.has(key)) return;
    seen.add(key);
    if (seen.size > 3000) seen.clear(); // 防止长直播内存膨胀（重新去重一轮）
    pending.push(item);
    if (pending.length >= CONFIG.maxBatch) flush();
  }

  function flush() {
    if (!pending.length) return;
    var batch = pending.splice(0, CONFIG.maxBatch);
    var body = {
      token: CONFIG.token,
      platform: 'browser',
      items: batch.map(function (it) {
        return {
          user_id: maskUser(it.user),
          content: it.content,
          sent_at: new Date().toISOString(),
          raw: { page_url: location.href }
        };
      })
    };
    fetch(CONFIG.server + '/api/v1/gateway/browser/ingest/' + CONFIG.sessionId, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (r) {
      if (r.status === 409) log('网关侧采集适配器未运行，请先为场次', CONFIG.sessionId, '启动 browser 适配器');
      else if (r.status === 401) log('回传令牌校验失败，请核对 token 配置');
      else if (r.ok) return r.json().then(function (j) { log('回传成功', j); });
      else log('回传失败 HTTP', r.status);
    }).catch(function (e) { log('回传异常（后端未启动？）', e); });
  }

  // 监听评论区新增节点
  var observer = new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      [].slice.call(m.addedNodes).forEach(function (n) {
        extract(n).forEach(queue);
      });
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });

  // 兜底轮询（部分平台弹幕容器节点复用而非新增）
  var lastText = '';
  setInterval(function () {
    var box = document.body.innerText || '';
    if (box.length > 200000) box = box.slice(-200000); // 只看尾部，防大页面卡顿
    if (box === lastText) return;
    lastText = box;
    box.split('\n').forEach(function (line) {
      line = line.trim();
      if (line && line.length <= 200) {
        var m = line.match(/^([^:：]{1,30})[:：]\s*(.+)$/);
        queue({ user: m ? m[1] : null, content: m ? m[2] : line });
      }
    });
  }, 5000);

  setInterval(flush, CONFIG.flushInterval);
  log('已启动 | 场次=' + CONFIG.sessionId + ' 回传至 ' + CONFIG.server);
})();
"""
