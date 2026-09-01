<template>
  <div class="sparkline">
    <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none">
      <!-- 参考基线 -->
      <line :x1="0" :x2="width" :y1="height / 2" :y2="height / 2" stroke="#ebeef5" stroke-width="1" />
      <polyline
        v-if="points.length > 1"
        :points="polylinePoints"
        fill="none"
        :stroke="color"
        stroke-width="1.8"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
      <circle v-if="lastPoint" :cx="lastPoint.x" :cy="lastPoint.y" r="2.6" :fill="color" />
    </svg>
    <div v-if="points.length < 2" class="empty-tip">暂无数据</div>
  </div>
</template>

<script setup>
// 轻量 SVG 折线（避免引入 ECharts 重依赖）：展示指标滑动窗口趋势
import { computed } from 'vue'

const props = defineProps({
  values: { type: Array, required: true }, // 按时间升序的数值序列
  width: { type: Number, default: 260 },
  height: { type: Number, default: 56 },
  color: { type: String, default: '#409eff' }
})

const PAD = 4

const points = computed(() => {
  const vals = props.values.filter(v => typeof v === 'number' && !Number.isNaN(v))
  if (vals.length < 2) return []
  let min = Math.min(...vals)
  let max = Math.max(...vals)
  if (min === max) { min -= 1; max += 1 }
  const spanX = props.width - PAD * 2
  const spanY = props.height - PAD * 2
  return vals.map((v, i) => ({
    x: PAD + (spanX * i) / (vals.length - 1),
    y: PAD + spanY * (1 - (v - min) / (max - min)),
    v
  }))
})

const polylinePoints = computed(() =>
  points.value.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
)
const lastPoint = computed(() => points.value[points.value.length - 1])
</script>

<style scoped>
.sparkline { position: relative; width: 100%; }
.sparkline svg { display: block; width: 100%; height: auto; }
.empty-tip {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  color: #c0c4cc; font-size: 12px;
}
</style>
