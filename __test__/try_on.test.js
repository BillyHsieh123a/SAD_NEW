// __tests__/try_on.test.js
/**
 * @jest-environment jsdom
 */

// Mock console methods
global.console.debug = jest.fn();
global.console.error = jest.fn();

// Mock fetch
global.fetch = jest.fn();

// Mock FileReader
global.FileReader = class {
  constructor() {
    this.onload = null;
    this.readAsDataURL = jest.fn((file) => {
      setTimeout(() => {
        if (this.onload) {
          this.onload({ target: { result: 'data:image/jpeg;base64,mockdata' } });
        }
      }, 0);
    });
  }
};

// Mock FormData
global.FormData = class {
  constructor() {
    this.data = new Map();
  }
  append(key, value) {
    this.data.set(key, value);
  }
  get(key) {
    return this.data.get(key);
  }
};

describe('Virtual Try-On App 基礎測試', () => {
  // 測試全域變數初始化
  let selectedClothes, currentCategory, selectedItems;

  beforeEach(() => {
    // 模擬 DOM 元素
    document.body.innerHTML = `
      <div id="tops-grid"></div>
      <div id="bottoms-grid"></div>
      <div id="user-image" class="hidden"></div>
      <div class="placeholder-text"></div>
      <div id="result-image" class="hidden"></div>
      <div id="result-placeholder"></div>
      <div id="ai-comment-text"></div>
      <div id="tryon-gallery"></div>
    `;

    // 初始化狀態
    selectedClothes = {
      tops: [],
      bottoms: [],
      user: null
    };
    currentCategory = 'tops';
    selectedItems = new Set();
    
    // 重置 fetch mock
    if (global.fetch) {
      global.fetch.mockClear();
    }
  });

  test('應該能初始化基本狀態', () => {
    expect(selectedClothes.tops).toEqual([]);
    expect(selectedClothes.bottoms).toEqual([]);
    expect(selectedClothes.user).toBeNull();
    expect(currentCategory).toBe('tops');
    expect(selectedItems.size).toBe(0);
  });

  test('應該能模擬新增服裝項目', () => {
    const item = {
      id: 123,
      src: 'test-shirt.jpg',
      name: 'Test Shirt',
      category: 'tops'
    };
    
    selectedClothes.tops.push(item);
    expect(selectedClothes.tops).toHaveLength(1);
    expect(selectedClothes.tops[0]).toEqual(item);
  });

  test('應該能模擬項目選擇邏輯', () => {
    const itemId1 = 123;
    const itemId2 = 456;
    
    // 模擬同類別只能選一個的邏輯
    function toggleItemSelection(id, category) {
      // 清除該類別的其他選擇
      selectedClothes[category].forEach(item => {
        selectedItems.delete(item.id);
      });
      
      // 切換當前項目
      if (!selectedItems.has(id)) {
        selectedItems.add(id);
        return true;
      } else {
        selectedItems.delete(id);
        return false;
      }
    }
    
    // 添加兩個項目到 tops
    selectedClothes.tops.push({ id: itemId1, src: 'shirt1.jpg', name: 'Shirt 1', category: 'tops' });
    selectedClothes.tops.push({ id: itemId2, src: 'shirt2.jpg', name: 'Shirt 2', category: 'tops' });
    
    // 選擇第一個項目
    const selected1 = toggleItemSelection(itemId1, 'tops');
    expect(selected1).toBe(true);
    expect(selectedItems.has(itemId1)).toBe(true);
    
    // 選擇第二個項目（應該取消第一個）
    const selected2 = toggleItemSelection(itemId2, 'tops');
    expect(selected2).toBe(true);
    expect(selectedItems.has(itemId1)).toBe(false);
    expect(selectedItems.has(itemId2)).toBe(true);
  });

  test('應該能模擬刪除項目', () => {
    const itemId = 123;
    selectedClothes.tops.push({ id: itemId, src: 'shirt.jpg', name: 'Shirt', category: 'tops' });
    selectedItems.add(itemId);
    
    expect(selectedClothes.tops).toHaveLength(1);
    expect(selectedItems.has(itemId)).toBe(true);
    
    // 模擬刪除邏輯
    selectedClothes.tops = selectedClothes.tops.filter(item => item.id !== itemId);
    selectedItems.delete(itemId);
    
    expect(selectedClothes.tops).toHaveLength(0);
    expect(selectedItems.has(itemId)).toBe(false);
  });

  test('應該能模擬類別切換', () => {
    expect(currentCategory).toBe('tops');
    
    currentCategory = 'bottoms';
    expect(currentCategory).toBe('bottoms');
  });

  test('應該能模擬設定用戶圖片', () => {
    const imageSrc = 'user-photo.jpg';
    selectedClothes.user = imageSrc;
    
    expect(selectedClothes.user).toBe(imageSrc);
  });

  test('應該能模擬清除用戶圖片', () => {
    selectedClothes.user = 'user-photo.jpg';
    expect(selectedClothes.user).toBe('user-photo.jpg');
    
    selectedClothes.user = null;
    expect(selectedClothes.user).toBeNull();
  });

  test('應該能模擬 DOM 操作', () => {
    const grid = document.getElementById('tops-grid');
    expect(grid).toBeTruthy();
    
    // 模擬添加元素
    const div = document.createElement('div');
    div.className = 'clothing-item';
    div.innerHTML = '<img src="test.jpg" alt="test">';
    grid.appendChild(div);
    
    expect(grid.children).toHaveLength(1);
    expect(grid.querySelector('.clothing-item')).toBeTruthy();
  });

  test('應該能模擬 FileReader', (done) => {
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' });
    const reader = new FileReader();
    
    reader.onload = (e) => {
      expect(e.target.result).toBe('data:image/jpeg;base64,mockdata');
      done();
    };
    
    reader.readAsDataURL(file);
  });

  test('應該能模擬 fetch API', async () => {
    const mockResponse = { success: true, presigned_url: 'test-url.jpg' };
    global.fetch.mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse)
    });

    const response = await fetch('/api/user-photo/upload');
    const data = await response.json();

    expect(fetch).toHaveBeenCalledWith('/api/user-photo/upload');
    expect(data).toEqual(mockResponse);
  });

  test('應該能模擬錯誤處理', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));

    try {
      await fetch('/api/test');
    } catch (error) {
      expect(error.message).toBe('Network error');
    }
  });

  test('應該能模擬完整的服裝管理流程', () => {
    // 新增項目
    selectedClothes.tops.push({ id: 1, src: 'shirt1.jpg', name: 'Shirt 1', category: 'tops' });
    selectedClothes.tops.push({ id: 2, src: 'shirt2.jpg', name: 'Shirt 2', category: 'tops' });
    selectedClothes.bottoms.push({ id: 3, src: 'pants1.jpg', name: 'Pants 1', category: 'bottoms' });
    
    // 計算數量
    const counts = {
      tops: selectedClothes.tops.length,
      bottoms: selectedClothes.bottoms.length
    };
    expect(counts.tops).toBe(2);
    expect(counts.bottoms).toBe(1);
    
    // 選擇項目
    selectedItems.add(1); // 選擇 tops
    selectedItems.add(3); // 選擇 bottoms
    expect(selectedItems.size).toBe(2);
    
    // 檢查選擇狀態
    expect(selectedItems.has(1)).toBe(true);
    expect(selectedItems.has(3)).toBe(true);
  });
});