<template>
  <div class="home">
    <el-row :gutter="20">
      <!-- 左侧：输入控制面板 -->
      <el-col :span="12">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>📊 直播数据输入</span>
              <div>
                <el-select v-model="testScenario" placeholder="选择测试场景" style="margin-right: 10px;">
                  <el-option label="默认场景" value="default" />
                  <el-option label="产品讲解期" value="product_intro" />
                  <el-option label="促单期" value="promotion" />
                  <el-option label="问答互动期" value="qna" />
                </el-select>
                <el-button type="primary" @click="simulateInput" :loading="loading">
                  填充测试数据
                </el-button>
              </div>
            </div>
          </template>

          <el-form label-width="120px">
            <!-- 直播状态 -->
            <el-divider content-position="left">直播状态</el-divider>
            <el-form-item label="当前阶段">
              <el-select v-model="inputData.直播状态.当前阶段" placeholder="选择阶段">
                <el-option label="预热期" value="预热期" />
                <el-option label="产品讲解期" value="产品讲解期" />
                <el-option label="促单期" value="促单期" />
                <el-option label="问答互动期" value="问答互动期" />
                <el-option label="结尾期" value="结尾期" />
              </el-select>
            </el-form-item>
            <el-form-item label="已直播时长(秒)">
              <el-input-number v-model="inputData.直播状态.已直播时长" :min="0" :step="60" />
            </el-form-item>
            <el-form-item label="计划总时长(秒)">
              <el-input-number v-model="inputData.直播状态.计划总时长" :min="0" :step="600" />
            </el-form-item>

            <!-- 弹幕数据 -->
            <el-divider content-position="left">弹幕数据</el-divider>
            <el-form-item label="最近30秒消息">
              <el-input
                v-model="danmuText"
                type="textarea"
                :rows="3"
                placeholder="每行一条弹幕，用回车分隔"
              />
            </el-form-item>

            <!-- 商品数据 -->
            <el-divider content-position="left">商品数据</el-divider>
            <el-form-item label="SKU ID">
              <el-input v-model="inputData.商品数据.sku_id" />
            </el-form-item>
            <el-form-item label="产品名称">
              <el-input v-model="inputData.商品数据.产品名称" />
            </el-form-item>
            <el-form-item label="价格">
              <el-input-number v-model="inputData.商品数据.价格" :min="0" />
            </el-form-item>
            <el-form-item label="成分（逗号分隔）">
              <el-input v-model="ingredientsText" placeholder="如水杨酸,烟酰胺" />
            </el-form-item>
            <el-form-item label="功效（逗号分隔）">
              <el-input v-model="effectsText" placeholder="如控油,修护" />
            </el-form-item>

            <!-- 后台数据 -->
            <el-divider content-position="left">后台数据</el-divider>
            <el-form-item label="在线人数">
              <el-input-number v-model="inputData.后台数据.在线人数" :min="0" />
            </el-form-item>

            <!-- 文件上传 -->
            <el-divider content-position="left">产品文档上传</el-divider>
            <el-form-item label="上传文档">
              <el-upload
                class="upload-demo"
                action="/api/v1/products/upload"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :file-list="fileList"
                :auto-upload="false"
                ref="upload"
              >
                <el-button type="primary">选择文件</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持上传 txt、md、pdf、doc、docx 格式的文件，用于构建产品知识库
                  </div>
                </template>
              </el-upload>
              <el-button type="info" @click="$refs.upload.submit()" style="margin-left: 10px;">
                上传并添加到知识库
              </el-button>
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="submitDecision" :loading="loading" size="large">
                🚀 获取提词建议
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：输出展示 -->
      <el-col :span="12">
        <el-card class="output-card">
          <template #header>
            <div class="card-header">
              <span>📢 提词建议输出</span>
              <el-tag :type="outputTagType">{{ outputData.提词指令?.优先级 || '待计算' }}</el-tag>
            </div>
          </template>

          <div v-if="outputData.提词指令" class="result-content">
            <el-alert
              :title="outputData.提词指令.触发原因"
              :type="outputData.提词指令.优先级 === '高' ? 'error' : 'warning'"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            />

            <!-- 直播内容结构信息 -->
            <div v-if="outputData.直播结构" class="stage-info" style="margin-bottom: 20px">
              <el-card class="stage-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>📅 直播结构信息</span>
                  </div>
                </template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="当前阶段">
                    <el-tag type="primary">{{ outputData.直播结构.当前阶段 }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="阶段描述">
                    {{ outputData.直播结构.阶段描述 }}
                  </el-descriptions-item>
                  <el-descriptions-item label="下一阶段">
                    {{ outputData.直播结构.下一阶段 || '无' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="阶段提示">
                    <el-tag v-for="(tip, index) in outputData.直播结构.阶段提示" :key="index" type="info" style="margin-right: 10px; margin-bottom: 10px">
                      {{ tip }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="下一阶段准备">
                    <el-tag v-for="(tip, index) in outputData.直播结构.下一阶段准备" :key="index" type="warning" style="margin-right: 10px; margin-bottom: 10px">
                      {{ tip }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="阶段切换建议">
                    {{ outputData.直播结构.阶段切换建议?.建议 || '无' }}
                    <div v-if="outputData.直播结构.阶段切换建议?.原因" style="margin-top: 5px; font-size: 14px; color: #606266">
                      原因: {{ outputData.直播结构.阶段切换建议?.原因 }}
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </div>

            <el-descriptions :column="1" border>
              <el-descriptions-item label="建议话术">
                <div class="speech-text">
                  {{ outputData.提词指令.建议话术 }}
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="动作建议">
                {{ outputData.提词指令.动作建议 || '无' }}
              </el-descriptions-item>
              <el-descriptions-item label="合规检查">
                <el-tag :type="outputData.提词指令.合规检查 === '通过' ? 'success' : 'danger'">
                  {{ outputData.提词指令.合规检查 }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <el-empty v-else description="点击左侧按钮获取提词建议" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { agentDecide } from '@/api'

// 加载状态
const loading = ref(false)

// 输入数据
const inputData = ref({
  直播状态: {
    当前阶段: '产品讲解期',
    已直播时长: 900,
    计划总时长: 3600,
    当前产品: '精华液_sku_12345'
  },
  弹幕数据: {
    最近30秒消息: [],
    情绪分析: {
      高频词: {},
      负面反馈: []
    }
  },
  商品数据: {
    sku_id: '12345',
    产品名称: '控油修护精华液',
    规格: '30ml',
    价格: 350,
    成分: [],
    功效: []
  },
  后台数据: {
    在线人数: 1250,
    购物车点击率: '上升5%',
    转化率: '2.3%'
  }
})

// 辅助字段
const danmuText = ref('')
const ingredientsText = ref('')
const effectsText = ref('')
const testScenario = ref('default')
const fileList = ref([])

// 输出数据
const outputData = ref({})

// 计算输出标签类型
const outputTagType = computed(() => {
  const priority = outputData.value.提词指令?.优先级
  if (priority === '高') return 'danger'
  if (priority === '中') return 'warning'
  return 'info'
})

// 文件上传成功处理
const handleUploadSuccess = (response, file, fileList) => {
  ElMessage.success('文件上传成功并添加到知识库')
  console.log('上传成功:', response)
}

// 文件上传失败处理
const handleUploadError = (error, file, fileList) => {
  ElMessage.error('文件上传失败')
  console.error('上传失败:', error)
}

// 解析弹幕文本
const parseDanmu = () => {
  const messages = danmuText.value.split('\n').filter(m => m.trim())
  inputData.value.弹幕数据.最近30秒消息 = messages

  // 简单情绪分析
  const highFreqWords = {}
  const negativeFeedback = []
  const negativeKeywords = ['贵', '太贵', '不好', '差', '坑', '骗']

  messages.forEach(msg => {
    // 统计高频词（简单按字符/词分割）
    msg.replace(/[\u4e00-\u9fa5]{2,}/g, (word) => {
      highFreqWords[word] = (highFreqWords[word] || 0) + 1
    })

    // 检测负面反馈
    if (negativeKeywords.some(kw => msg.includes(kw))) {
      negativeFeedback.push(msg)
    }
  })

  inputData.value.弹幕数据.情绪分析 = {
    高频词: highFreqWords,
    负面反馈: negativeFeedback
  }
}

// 解析商品属性
const parseProduct = () => {
  inputData.value.商品数据.成分 = ingredientsText.value.split(',').map(s => s.trim()).filter(s => s)
  inputData.value.商品数据.功效 = effectsText.value.split(',').map(s => s.trim()).filter(s => s)
}

// 提交决策
const submitDecision = async () => {
  parseDanmu()
  parseProduct()

  loading.value = true
  try {
    const response = await agentDecide(inputData.value)
    outputData.value = response
    ElMessage.success('获取提词建议成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('获取提词建议失败: ' + (error.message || error))
  } finally {
    loading.value = false
  }
}

// 模拟数据
const simulateInput = () => {
  switch (testScenario.value) {
    case 'default':
      inputData.value.直播状态.当前阶段 = '产品讲解期'
      inputData.value.商品数据 = {
        sku_id: '12345',
        产品名称: '控油修护精华液',
        规格: '30ml',
        价格: 350,
        成分: [],
        功效: []
      }
      danmuText.value = '油皮能用吗？\n有没有小样？\n价格太贵了\n油皮能用吗？\n和XX大牌比怎么样？\n油皮能用吗？'
      ingredientsText.value = '水杨酸,烟酰胺,透明质酸'
      effectsText.value = '控油,修护,保湿'
      break
    case 'product_intro':
      inputData.value.直播状态.当前阶段 = '产品讲解期'
      inputData.value.商品数据 = {
        sku_id: '12346',
        产品名称: '焕白精华液',
        规格: '50ml',
        价格: 480,
        成分: [],
        功效: []
      }
      danmuText.value = '这个产品有什么功效？\n适合什么肤质？\n成分安全吗？\n这个产品有什么功效？\n怎么使用？\n这个产品有什么功效？'
      ingredientsText.value = '水杨酸,烟酰胺,透明质酸,维生素C'
      effectsText.value = '控油,修护,保湿,美白'
      break
    case 'promotion':
      inputData.value.直播状态.当前阶段 = '促单期'
      inputData.value.商品数据 = {
        sku_id: '12347',
        产品名称: '抗皱紧致精华液',
        规格: '30ml',
        价格: 680,
        成分: [],
        功效: []
      }
      danmuText.value = '有优惠吗？\n怎么下单？\n什么时候发货？\n有优惠吗？\n有赠品吗？\n有优惠吗？'
      ingredientsText.value = '视黄醇,胜肽,透明质酸'
      effectsText.value = '抗皱,紧致,保湿'
      break
    case 'qna':
      inputData.value.直播状态.当前阶段 = '问答互动期'
      inputData.value.商品数据 = {
        sku_id: '12348',
        产品名称: '舒缓修护精华液',
        规格: '30ml',
        价格: 320,
        成分: [],
        功效: []
      }
      danmuText.value = '敏感肌能用吗？\n孕妇能用吗？\n能和其他产品一起用吗？\n敏感肌能用吗？\n效果怎么样？\n敏感肌能用吗？'
      ingredientsText.value = '神经酰胺,积雪草,透明质酸'
      effectsText.value = '舒缓,修护,保湿'
      break
  }
  ElMessage.success('已填充测试数据')
}
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
}

.input-card,
.output-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.result-content {
  padding: 10px;
}

.speech-text {
  font-size: 16px;
  line-height: 1.8;
  color: #303133;
  padding: 10px;
  background-color: #f0f9eb;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}
</style>
