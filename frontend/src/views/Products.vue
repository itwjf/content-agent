<template>
  <div class="products">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchSku"
            placeholder="输入SKU ID搜索"
            clearable
            @keyup.enter="searchProducts"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="8">
          <el-button type="primary" @click="searchProducts">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-col>
        <el-col :span="8" style="text-align: right">
          <el-button type="success" @click="openDialog('add')">
            <el-icon><Plus /></el-icon> 添加商品
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 商品列表 -->
    <el-card class="table-card">
      <el-table :data="filteredProducts" stripe style="width: 100%">
        <el-table-column prop="sku_id" label="SKU ID" width="120" />
        <el-table-column prop="name" label="商品名称" min-width="180" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="brand" label="品牌" width="100" />
        <el-table-column prop="spec" label="规格" width="80" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="scope">
            <span style="color: #f56c6c; font-weight: bold">¥{{ scope.row.price }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="original_price" label="原价" width="100">
          <template #default="scope">
            <span v-if="scope.row.original_price" style="text-decoration: line-through; color: #909399">
              ¥{{ scope.row.original_price }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="功效" min-width="150">
          <template #default="scope">
            <el-tag v-for="effect in scope.row.effects" :key="effect" size="small" style="margin-right: 5px">
              {{ effect }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewProduct(scope.row)">查看</el-button>
            <el-button size="small" type="primary" @click="editProduct(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteProduct(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="productForm" label-width="100px" :rules="formRules" ref="formRef">
        <el-form-item label="SKU ID" prop="sku_id">
          <el-input v-model="productForm.sku_id" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="productForm.name" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="productForm.category" placeholder="选择分类">
                <el-option label="护肤品" value="护肤品" />
                <el-option label="彩妆" value="彩妆" />
                <el-option label="洗护" value="洗护" />
                <el-option label="美容仪器" value="美容仪器" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品牌" prop="brand">
              <el-input v-model="productForm.brand" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规格" prop="spec">
              <el-input v-model="productForm.spec" placeholder="如 30ml" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number v-model="productForm.price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="原价" prop="original_price">
          <el-input-number v-model="productForm.original_price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="成分" prop="ingredients">
          <el-input v-model="ingredientsText" placeholder="多个成分用逗号分隔" />
        </el-form-item>
        <el-form-item label="功效" prop="effects">
          <el-input v-model="effectsText" placeholder="多个功效用逗号分隔" />
        </el-form-item>
        <el-form-item label="卖点" prop="selling_points">
          <el-input v-model="sellingPointsText" type="textarea" :rows="2" placeholder="多个卖点用逗号分隔" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="productForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ dialogMode === 'add' ? '添加' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 商品详情对话框 -->
    <el-dialog v-model="viewDialogVisible" title="商品详情" width="600px">
      <el-descriptions :column="1" border v-if="currentProduct">
        <el-descriptions-item label="SKU ID">{{ currentProduct.sku_id }}</el-descriptions-item>
        <el-descriptions-item label="商品名称">{{ currentProduct.name }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ currentProduct.category }}</el-descriptions-item>
        <el-descriptions-item label="品牌">{{ currentProduct.brand }}</el-descriptions-item>
        <el-descriptions-item label="规格">{{ currentProduct.spec }}</el-descriptions-item>
        <el-descriptions-item label="价格">
          <span style="color: #f56c6c; font-weight: bold">¥{{ currentProduct.price }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="原价">
          <span v-if="currentProduct.original_price" style="text-decoration: line-through">
            ¥{{ currentProduct.original_price }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="成分">
          <el-tag v-for="item in currentProduct.ingredients" :key="item" size="small" style="margin-right: 5px">
            {{ item }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="功效">
          <el-tag v-for="item in currentProduct.effects" :key="item" type="success" size="small" style="margin-right: 5px">
            {{ item }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="卖点">
          <el-tag v-for="item in currentProduct.selling_points" :key="item" type="warning" size="small" style="margin-right: 5px">
            {{ item }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentProduct.description }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getProducts, getProduct, createProduct, deleteProduct as deleteProductApi } from '@/api'

// 数据
const products = ref([])
const searchSku = ref('')
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const dialogMode = ref('add') // add 或 edit
const currentProduct = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const productForm = ref({
  sku_id: '',
  name: '',
  category: '',
  brand: '',
  spec: '',
  price: 0,
  original_price: null,
  ingredients: [],
  effects: [],
  selling_points: [],
  description: ''
})

// 辅助文本字段
const ingredientsText = ref('')
const effectsText = ref('')
const sellingPointsText = ref('')

// 表单验证规则
const formRules = {
  sku_id: [{ required: true, message: '请输入 SKU ID', trigger: 'blur' }],
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }]
}

// 计算属性
const filteredProducts = computed(() => {
  if (!searchSku.value) return products.value
  return products.value.filter(p => p.sku_id.includes(searchSku.value))
})

const dialogTitle = computed(() => {
  return dialogMode.value === 'add' ? '添加商品' : '编辑商品'
})

// 方法
const loadProducts = async () => {
  try {
    const res = await getProducts()
    products.value = res || []
  } catch (error) {
    console.error('加载商品失败:', error)
    ElMessage.error('加载商品失败')
  }
}

const searchProducts = () => {
  // 搜索功能通过计算属性实现
}

const resetSearch = () => {
  searchSku.value = ''
}

const openDialog = (mode) => {
  dialogMode.value = mode
  dialogVisible.value = true
  resetForm()
}

const resetForm = () => {
  productForm.value = {
    sku_id: '',
    name: '',
    category: '',
    brand: '',
    spec: '',
    price: 0,
    original_price: null,
    ingredients: [],
    effects: [],
    selling_points: [],
    description: ''
  }
  ingredientsText.value = ''
  effectsText.value = ''
  sellingPointsText.value = ''
}

const viewProduct = (row) => {
  currentProduct.value = row
  viewDialogVisible.value = true
}

const editProduct = (row) => {
  dialogMode.value = 'edit'
  productForm.value = { ...row }
  ingredientsText.value = (row.ingredients || []).join(', ')
  effectsText.value = (row.effects || []).join(', ')
  sellingPointsText.value = (row.selling_points || []).join(', ')
  dialogVisible.value = true
}

const deleteProduct = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除商品 "${row.name}" 吗？`, '提示', {
      type: 'warning'
    })
    await deleteProductApi(row.sku_id)
    ElMessage.success('删除成功')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 解析文本字段
      const data = {
        ...productForm.value,
        ingredients: ingredientsText.value.split(',').map(s => s.trim()).filter(s => s),
        effects: effectsText.value.split(',').map(s => s.trim()).filter(s => s),
        selling_points: sellingPointsText.value.split(',').map(s => s.trim()).filter(s => s)
      }
      
      await createProduct(data)
      ElMessage.success(dialogMode.value === 'add' ? '添加成功' : '保存成功')
      dialogVisible.value = false
      loadProducts()
    } catch (error) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 生命周期
onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.products {
  max-width: 1400px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}
</style>
