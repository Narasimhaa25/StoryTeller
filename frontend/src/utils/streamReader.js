export default async function readStream(response, onChunk) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    if (!chunk.startsWith("[typing]")) {
      onChunk(chunk);
    }
  }
}