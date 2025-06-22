import { Agent } from "@huggingface/tiny-agents";

const agent = new Agent({
  provider: process.env.PROVIDER ?? "nebius",
  model: process.env.MODEL_ID ?? "Qwen/Qwen2.5-72B-Instruct",
  apiKey: process.env.HUGGINGFACE_API_TOKEN,
  servers: [
    {
      command: "npx",
      args: ["mcp-remote", "http://localhost:7860/gradio_api/mcp/sse"],
    },
  ],
});

await agent.loadTools();

for await (const chunk of agent.run("She was sad because she had lost her favorite toy.")) {
    console.log(chunk)
}
