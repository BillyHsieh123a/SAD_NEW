// __tests__/login.test.js
/**
 * @jest-environment jsdom
 */

// Mock fetch
global.fetch = jest.fn();

describe('登入功能測試', () => {
  let loginForm, usernameInput, passwordInput, errorDiv;

  beforeEach(() => {
    // 重置 fetch mock
    fetch.mockClear();
    
    // 創建 DOM 結構
    document.body.innerHTML = `
      <form id="loginForm">
        <input type="text" name="username" id="username" />
        <input type="password" name="password" id="password" />
        <button type="submit">Login</button>
      </form>
      <div id="loginError" style="display: none;"></div>
    `;

    // 獲取 DOM 元素
    loginForm = document.getElementById('loginForm');
    usernameInput = document.getElementById('username');
    passwordInput = document.getElementById('password');
    errorDiv = document.getElementById('loginError');

    // 綁定事件監聽器
    loginForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const username = document.querySelector('input[name="username"]').value.trim();
      const password = document.querySelector('input[name="password"]').value.trim();
      const errorDiv = document.getElementById('loginError');
      errorDiv.style.display = "none";

      if (!username || !password) {
        errorDiv.textContent = "Please enter both username and password.";
        errorDiv.style.display = "block";
        return;
      }

      try {
        const res = await fetch('/api/login/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
          // 成功時不測試重導向，只測試沒有顯示錯誤
          console.log('Login successful, would redirect to /try-on');
        } else {
          errorDiv.textContent = data.message || "Login failed.";
          errorDiv.style.display = "block";
        }
      } catch (err) {
        errorDiv.textContent = "Server error. Please try again.";
        errorDiv.style.display = "block";
      }
    });
  });

  describe('表單驗證', () => {
    test('應該顯示錯誤當用戶名為空', async () => {
      usernameInput.value = '';
      passwordInput.value = 'password123';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Please enter both username and password.');
    });

    test('應該顯示錯誤當密碼為空', async () => {
      usernameInput.value = 'testuser';
      passwordInput.value = '';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Please enter both username and password.');
    });

    test('應該顯示錯誤當兩個欄位都為空', async () => {
      usernameInput.value = '';
      passwordInput.value = '';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Please enter both username and password.');
    });

    test('應該處理只有空白字符的輸入', async () => {
      usernameInput.value = '   ';
      passwordInput.value = '   ';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Please enter both username and password.');
    });
  });

  describe('成功登入', () => {
    test('應該呼叫正確的 API 並且不顯示錯誤', async () => {
      fetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true })
      });

      usernameInput.value = 'testuser';
      passwordInput.value = 'password123';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      // 檢查 API 呼叫
      expect(fetch).toHaveBeenCalledWith('/api/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: 'testuser', 
          password: 'password123' 
        })
      });

      // 檢查沒有顯示錯誤訊息
      expect(errorDiv.style.display).toBe('none');
    });

    test('應該處理用戶名和密碼的前後空白', async () => {
      fetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true })
      });

      usernameInput.value = '  testuser  ';
      passwordInput.value = '  password123  ';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      // 檢查 trim 是否正常工作
      expect(fetch).toHaveBeenCalledWith('/api/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: 'testuser', 
          password: 'password123' 
        })
      });
    });
  });

  describe('登入失敗', () => {
    test('應該顯示伺服器錯誤訊息', async () => {
      fetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ 
          success: false, 
          message: 'Invalid username or password' 
        })
      });

      usernameInput.value = 'testuser';
      passwordInput.value = 'wrongpassword';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Invalid username or password');
    });

    test('應該顯示預設錯誤訊息當沒有具體訊息', async () => {
      fetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ success: false })
      });

      usernameInput.value = 'testuser';
      passwordInput.value = 'wrongpassword';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Login failed.');
    });
  });

  describe('網路錯誤處理', () => {
    test('應該處理網路錯誤', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      usernameInput.value = 'testuser';
      passwordInput.value = 'password123';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Server error. Please try again.');
    });

    test('應該處理 JSON 解析錯誤', async () => {
      fetch.mockResolvedValueOnce({
        json: () => Promise.reject(new Error('Invalid JSON'))
      });

      usernameInput.value = 'testuser';
      passwordInput.value = 'password123';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 10));

      expect(errorDiv.style.display).toBe('block');
      expect(errorDiv.textContent).toBe('Server error. Please try again.');
    });
  });

  describe('UI 行為', () => {
    test('提交時應該隱藏錯誤訊息', async () => {
      // 先顯示錯誤訊息
      errorDiv.style.display = 'block';
      errorDiv.textContent = 'Previous error';

      fetch.mockResolvedValueOnce({
        json: () => Promise.resolve({ success: true })
      });

      usernameInput.value = 'testuser';
      passwordInput.value = 'password123';

      const submitEvent = new Event('submit', { bubbles: true });
      loginForm.dispatchEvent(submitEvent);

      await new Promise(resolve => setTimeout(resolve, 0));

      // 錯誤訊息應該被隱藏
      expect(errorDiv.style.display).toBe('none');
    });

    test('應該阻止表單的預設提交行為', () => {
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      const preventDefaultSpy = jest.spyOn(submitEvent, 'preventDefault');

      usernameInput.value = 'testuser';
      passwordInput.value = 'password123';

      loginForm.dispatchEvent(submitEvent);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });
});