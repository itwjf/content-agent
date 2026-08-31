"""
展示服务
导演脚本 → [合规硬闸门] → TTS 音频 + 字幕 JSON + 动作指令包 →（可选）数字人形象驱动
无 GPU/驱动未就绪时自动降级为"TTS + 字幕"纯声音形态
"""
import asyncio
from typing import Optional

from loguru import logger

from app.core.config import get_settings
from app.services.director.models import DirectorScript
from app.services.modules.compliance_module import compliance_module
from app.services.showcase.avatar import get_avatar_adapter
from app.services.showcase.tts import get_tts_adapter


class ShowcaseService:
    """展示适配服务"""

    def __init__(self):
        self.settings = get_settings()

    async def present(self, script: DirectorScript) -> dict:
        """将导演脚本转换为可播出内容包

        Returns:
            {
              "session_id", "record_key",
              "compliance_gate": {"passed", "blocked_lines", "corrected"},
              "mode": "avatar" | "audio_subtitle" | "blocked",
              "ai_label": bool,
              "subtitles": [{index, text, emotion, pace, audio_url, duration_ms}],
              "action_commands": [...],
              "avatar": {"video_url"} | None,
              "show_product_card", "product_sku", "priority"
            }
        """
        tts = get_tts_adapter()

        # ---- 1. 合规硬闸门：违禁词且无可用替代 → 该句拦截不出声 ----
        subtitles = []
        blocked_lines = []
        corrected_any = False
        for idx, line in enumerate(script.lines):
            check = compliance_module.check(line.text)
            text = line.text
            if not check["passed"]:
                if check["suggestion"] and check["suggestion"] != line.text:
                    text = check["suggestion"]  # 有替代方案 → 替换后放行
                    corrected_any = True
                else:
                    blocked_lines.append({"index": idx, "text": line.text})
                    continue
            # ---- 2. TTS 合成（阻塞调用放线程池）----
            try:
                tts_result = await asyncio.to_thread(tts.synthesize, text, line.emotion, line.pace)
            except Exception as e:
                logger.error(f"[展示] TTS 合成异常: {e}")
                continue
            subtitles.append({
                "index": idx,
                "text": text,
                "emotion": line.emotion,
                "pace": line.pace,
                "audio_url": tts_result.audio_url,
                "duration_ms": tts_result.duration_ms,
            })

        # ---- 3. 全部被拦截 → blocked，链路告警 ----
        mode = "audio_subtitle"
        avatar_info = None
        if not subtitles:
            logger.warning(f"[展示] 场次 {script.session_id} 台词全部被合规拦截，本轮不出声")
            return self._package(script, mode="blocked", subtitles=[], avatar_info=None,
                                 blocked_lines=blocked_lines, corrected=False)

        # ---- 4. 数字人形象驱动（未启用/失败自动降级为纯声音形态）----
        primary = subtitles[0]
        avatar = get_avatar_adapter()
        avatar_result = await asyncio.to_thread(
            avatar.render, primary["audio_url"], primary["emotion"]
        )
        if avatar_result:
            mode = "avatar"
            avatar_info = {"video_url": avatar_result.video_url}

        return self._package(script, mode=mode, subtitles=subtitles, avatar_info=avatar_info,
                             blocked_lines=blocked_lines, corrected=corrected_any)

    def _package(self, script: DirectorScript, mode: str, subtitles: list,
                 avatar_info: Optional[dict], blocked_lines: list, corrected: bool) -> dict:
        # 动作指令包：将台词动作建议映射为画面层操作
        action_commands = []
        for sub in subtitles:
            if sub.get("emotion"):
                action_commands.append({"type": "emotion", "value": sub["emotion"], "subtitle_index": sub["index"]})
        for line in script.lines:
            if line.action:
                action_commands.append({"type": "camera_action", "value": line.action})
        if script.show_product_card:
            action_commands.append({"type": "show_product_card", "value": script.product_sku})

        return {
            "session_id": script.session_id,
            "record_key": f"{script.session_id}-{script.created_at.isoformat()}",
            "compliance_gate": {
                "passed": len(blocked_lines) == 0,
                "blocked_lines": blocked_lines,
                "corrected": corrected,
            },
            "mode": mode,
            "ai_label": self.settings.avatar_ai_label,  # "AI 生成内容"标识
            "subtitles": subtitles,
            "action_commands": action_commands,
            "avatar": avatar_info,
            "show_product_card": script.show_product_card,
            "product_sku": script.product_sku,
            "priority": script.priority,
            "trigger_reason": script.trigger_reason,
        }


# 服务实例
showcase_service = ShowcaseService()
