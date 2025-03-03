import unittest
import json
from app.api.chat import yield_data

class TestYieldData(unittest.TestCase):
    def setUp(self):
        """设置测试数据"""
        self.test_id = "test-123"
        self.test_time = 1677649420
        self.test_model = "gpt-3.5-turbo"
        self.test_message = "Hello, world!"

    def test_first_message(self):
        """测试首条消息格式化"""
        result = yield_data(
            self.test_id,
            self.test_time,
            self.test_model,
            self.test_message,
            s_type="first"
        )
        
        # 解析返回的 SSE 数据
        data = json.loads(result.replace('data: ', '').strip())
        
        self.assertEqual(data['id'], self.test_id)
        self.assertEqual(data['object'], "chat.completion.chunk")
        self.assertEqual(data['created'], self.test_time)
        self.assertEqual(data['model'], self.test_model)
        self.assertEqual(len(data['choices']), 1)
        self.assertEqual(data['choices'][0]['index'], 0)
        self.assertEqual(data['choices'][0]['delta']['role'], "assistant")
        self.assertEqual(data['choices'][0]['delta']['content'], self.test_message)
        self.assertIsNone(data['choices'][0]['finish_reason'])

    def test_finish_message(self):
        """测试完成消息格式化"""
        result = yield_data(
            self.test_id,
            self.test_time,
            self.test_model,
            self.test_message,
            s_type="finish"
        )
        
        data = json.loads(result.replace('data: ', '').strip())
        
        self.assertEqual(data['id'], self.test_id)
        self.assertEqual(data['object'], "chat.completion.chunk")
        self.assertEqual(data['created'], self.test_time)
        self.assertEqual(data['model'], self.test_model)
        self.assertEqual(len(data['choices']), 1)
        self.assertEqual(data['choices'][0]['index'], 0)
        self.assertEqual(data['choices'][0]['delta'], {})
        self.assertEqual(data['choices'][0]['finish_reason'], "stop")

    def test_end_message(self):
        """测试结束消息格式化"""
        result = yield_data(
            self.test_id,
            self.test_time,
            self.test_model,
            self.test_message,
            s_type="end"
        )
        
        self.assertEqual(result, 'data: [DONE]\n\n')

    def test_normal_message(self):
        """测试普通消息格式化"""
        result = yield_data(
            self.test_id,
            self.test_time,
            self.test_model,
            self.test_message
        )
        
        data = json.loads(result.replace('data: ', '').strip())
        
        self.assertEqual(data['id'], self.test_id)
        self.assertEqual(data['object'], "chat.completion.chunk")
        self.assertEqual(data['created'], self.test_time)
        self.assertEqual(data['model'], self.test_model)
        self.assertEqual(len(data['choices']), 1)
        self.assertEqual(data['choices'][0]['index'], 0)
        self.assertEqual(data['choices'][0]['delta']['content'], self.test_message)
        self.assertIsNone(data['choices'][0]['finish_reason'])

    def test_empty_message(self):
        """测试空消息处理"""
        result = yield_data(
            self.test_id,
            self.test_time,
            self.test_model,
            ""
        )
        
        data = json.loads(result.replace('data: ', '').strip())
        self.assertEqual(data['choices'][0]['delta']['content'], "")

if __name__ == '__main__':
    unittest.main()