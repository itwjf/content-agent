<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>🎯 ContentAgent 智能直播辅助系统</h1>
          <el-menu
            mode="horizontal"
            :default-active="activeMenu"
            router
            class="header-menu"
          >
            <el-menu-item index="/">提词Demo</el-menu-item>
            <el-menu-item index="/products">商品管理</el-menu-item>
          </el-menu>
          <el-tag type="success">Agent Demo</el-tag>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  font-size: 20px;
  color: #303133;
}

.header-menu {
  flex: 1;
  margin: 0 20px;
  border: none;
}

.el-main {
  padding: 20px;
}
</style>
