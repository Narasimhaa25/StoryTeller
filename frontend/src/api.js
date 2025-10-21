export async function sendMessage(session, message) {
  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session, message })
  });

  const data = await res.json();
  return data.story || data.reply || data.error || "No response";
}