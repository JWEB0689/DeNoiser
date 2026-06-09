const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors());
app.use(express.json({ limit: '10mb' }));

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'rtk-engine', version: '1.0.0' });
});

/**
 * RTK Compression Engine Endpoint
 * Takes a history of messages and compresses the context based on given parameters.
 */
app.post('/api/compress', (req, res) => {
  const { messages, rtkConfig } = req.body;

  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: 'Messages array is required' });
  }

  if (!rtkConfig || !rtkConfig.enabled) {
    // If RTK is not enabled or provided, return the original payload unchanged
    return res.json({
      compressedMessages: messages,
      stats: { originalLength: messages.length, compressedLength: messages.length, compressionRatio: 0 }
    });
  }

  // --- Real-Time Knowledge Compression Algorithm (Simulated for Now) ---
  console.log(`[RTK-ENGINE] Received compression request: window=${rtkConfig.slidingWindowSize}, ratio=${rtkConfig.compressionRatio}`);
  
  // 1. Always keep system prompts
  const systemMessages = messages.filter(m => m.role === 'system');
  
  // 2. Extract recent interaction history (Sliding Window logic)
  const conversationMessages = messages.filter(m => m.role !== 'system');
  
  // Approximate a simple sliding window: only keep the most recent 'N' messages
  // (In a production Python backend with `tiktoken`, this would be based on actual token counts)
  const windowCount = Math.max(1, Math.floor(conversationMessages.length * rtkConfig.compressionRatio));
  const recentMessages = conversationMessages.slice(-windowCount);

  // 3. Assemble the compressed context
  const compressedMessages = [...systemMessages, ...recentMessages];

  console.log(`[RTK-ENGINE] Compressed ${messages.length} messages down to ${compressedMessages.length} messages.`);

  res.json({
    compressedMessages,
    stats: {
      originalLength: messages.length,
      compressedLength: compressedMessages.length,
      compressionRatio: rtkConfig.compressionRatio,
      slidingWindowSize: rtkConfig.slidingWindowSize
    }
  });
});

/**
 * Autonomous Bypass Strategy Endpoint
 * Routes requests to alternative LLM providers securely.
 */
app.post('/api/proxy', (req, res) => {
  const { rtkConfig, payload } = req.body;
  
  if (!rtkConfig || !rtkConfig.dynamicBypass) {
    return res.status(400).json({ error: 'Autonomous Bypass is disabled' });
  }

  console.log(`[RTK-ENGINE] Routing autonomous proxy payload via: ${rtkConfig.modelRoute}`);
  
  // Simulated proxy response
  setTimeout(() => {
    res.json({
      status: 'success',
      provider: rtkConfig.modelRoute,
      response: `Simulated proxy response from ${rtkConfig.modelRoute}. In a production environment, this engine will forward the payload using proprietary API keys hidden from the frontend client.`
    });
  }, 500);
});

app.listen(PORT, () => {
  console.log(`[RTK-ENGINE] Server listening on port ${PORT}`);
  console.log(`[RTK-ENGINE] Context Compressor API ready`);
});
