import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, FileDown, Loader2, Send } from 'lucide-react';

function DataTable({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) return <div>No data found.</div>;
  const headers = Object.keys(data[0]);
  return (
    <div className="overflow-x-auto overflow-y-auto max-h-64">
      <table className="min-w-full border text-xs text-left text-gray-700 bg-white">
        <thead className="bg-gray-100 sticky top-0 z-10">
          <tr>
            {headers.map(h => (
              <th key={h} className="px-3 py-2 border-b font-semibold whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {headers.map(h => (
                <td key={h} className="px-3 py-2 border-b whitespace-nowrap">{row[h]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MarkdownTableWithExport({ tableData, filename }) {
  const [showAll, setShowAll] = useState(false);
  const hasMore = Array.isArray(tableData) && tableData.length > 10;
  const visibleData = showAll || !Array.isArray(tableData) ? tableData : tableData.slice(0, 10);

  const handleExport = () => {
    import('xlsx').then(XLSX => {
      const ws = XLSX.utils.json_to_sheet(tableData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
      XLSX.writeFile(wb, filename || 'data.xlsx');
    });
  };

  return (
    <div className="mb-2">
      <button onClick={handleExport} className="mb-2 px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded flex items-center text-sm font-semibold gap-1">
        <FileDown size={18} /> Export as XLSX
      </button>
      {Array.isArray(visibleData) && visibleData.length > 0 ? <DataTable data={visibleData} /> : <div>No data found.</div>}
      {hasMore && (
        <button onClick={() => setShowAll(v => !v)} className="mt-1 text-blue-600 hover:underline text-xs">
          {showAll ? 'Show less' : `Show more (${tableData.length - 10} more rows)`}
        </button>
      )}
    </div>
  );
}

function Message({ role, text, tableData, filename, showTable }) {
  // Only render table if showTable is true and tableData is a non-empty array
  const isTable = showTable && Array.isArray(tableData) && tableData.length > 0;
  return (
    <div className={`flex w-full py-2 ${role === 'user' ? 'justify-end' : 'justify-start'}`}>
      {role === 'bot' && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 mr-3">
          <Bot size={22} />
        </div>
      )}
      <div className={`p-3 my-1 max-w-2xl w-fit rounded-2xl shadow ${role === 'user' ? 'bg-blue-600 text-white rounded-br-none ml-auto' : 'bg-white text-gray-900 rounded-bl-none mr-auto border border-gray-200'}`}
        style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
        {role === 'bot' && isTable ? (
          <MarkdownTableWithExport tableData={tableData} filename={filename} />
        ) : role === 'bot' ? <ReactMarkdown>{text}</ReactMarkdown> : text}
      </div>
      {role === 'user' && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600 ml-3">
          <User size={22} />
        </div>
      )}
    </div>
  );
}

function Loader() {
  return (
    <div className="flex justify-center items-center py-4">
      <Loader2 className="animate-spin text-blue-400" size={28} />
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I am your E-commerce AI assistant. How can I help you today?' }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetchTable, setFetchTable] = useState(false);
  const chatRef = useRef(null);
  const scrollToBottomRef = useRef(null);

  useEffect(() => {
    if (scrollToBottomRef.current) {
      scrollToBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', text: input, showTable: fetchTable };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg.text, fetch_table: fetchTable })
      });
      const data = await res.json();
      let tableData = null;
      if (data.tableData && Array.isArray(data.tableData) && data.tableData.length > 0) {
        tableData = data.tableData;
      } else if (data.result && Array.isArray(data.result) && data.result.length > 0 && typeof data.result[0] === 'object') {
        tableData = data.result;
      }
      const botMsg = {
        role: 'bot',
        text: data.answer || data.result?.answer || data.result?.error || JSON.stringify(data.result) || "No response",
        tableData,
        filename: 'result.xlsx',
        showTable: fetchTable
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', text: "Error: Could not reach server" }]);
    }
    setLoading(false);
  };


// const sendMessage = async () => {
//   if (!input.trim()) return;
//   const userMsg = { role: 'user', text: input, showTable: fetchTable };
//   setMessages(prev => [...prev, userMsg]);
//   setInput("");
//   setLoading(true);

//   const botMsg = {
//     role: 'bot',
//     text: "",
//     tableData: null,
//     filename: 'result.xlsx',
//     showTable: fetchTable
//   };
//   setMessages(prev => [...prev, botMsg]);
//   const botMsgIndex = messages.length + 1;

//   try {
//     const res = await fetch("http://localhost:8000/ask", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({ question: input, fetch_table: fetchTable })
//     });

//     const reader = res.body.getReader();
//     const decoder = new TextDecoder("utf-8");
//     let streamText = "";
//     let isFinalJson = false;

//     while (true) {
//       const { value, done } = await reader.read();
//       if (done) break;

//       const chunk = decoder.decode(value, { stream: true });

//       if (chunk.includes('[[END_JSON]]')) {
//         const [answerPart, jsonPart] = chunk.split('[[END_JSON]]');
//         streamText += answerPart;

//         // ✅ Parse final metadata
//         const meta = JSON.parse(jsonPart);
//         const tableData = meta.tableData || meta.result;

//         setMessages(prev => {
//           const updated = [...prev];
//           updated[botMsgIndex] = {
//             ...updated[botMsgIndex],
//             text: streamText.trim(),
//             tableData,
//             showTable: fetchTable
//           };
//           return updated;
//         });

//         isFinalJson = true;
//         break;
//       }

//       streamText += chunk;

//       // ✅ Update live streaming answer
//       setMessages(prev => {
//         const updated = [...prev];
//         updated[botMsgIndex] = {
//           ...updated[botMsgIndex],
//           text: streamText
//         };
//         return updated;
//       });
//     }

//     // Fallback: If for some reason [[END_JSON]] is missing
//     if (!isFinalJson) {
//       setMessages(prev => {
//         const updated = [...prev];
//         updated[botMsgIndex] = {
//           ...updated[botMsgIndex],
//           text: streamText.trim()
//         };
//         return updated;
//       });
//     }

//   } catch (e) {
//     setMessages(prev => [...prev, { role: "bot", text: "Error: Could not reach server" }]);
//   }

//   setLoading(false);
// };



  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 flex flex-col">
      <header className="w-full py-4 px-6 bg-white shadow flex items-center justify-between sticky top-0 z-10 border-b">
        <div className="flex items-center gap-2">
          <Bot className="text-blue-600" size={28} />
          <span className="font-bold text-2xl text-gray-800 tracking-tight">E-commerce AI Chat</span>
        </div>
        {/* <a href="https://github.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm">GitHub</a> */}
      </header>
      <main className="flex-1 flex flex-col items-center justify-center px-2">
        <div ref={chatRef} className="w-full max-w-5xl flex-1 overflow-y-auto bg-white rounded-xl shadow p-6 my-8 border" style={{height: '75vh'}}>
          {messages.map((msg, idx) => <Message key={idx} {...msg} />)}
          {loading && <Loader />}
          <div ref={scrollToBottomRef} />
        </div>
      </main>
      <form className="w-full max-w-5xl mx-auto flex items-center gap-2 px-2 pb-8 sticky bottom-0 bg-white" onSubmit={e => { e.preventDefault(); sendMessage(); }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 p-4 border rounded-2xl shadow resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white min-h-[48px] max-h-40 text-base"
          placeholder="Ask a question about your e-commerce data..."
          rows={1}
        />
        <button
          type="button"
          className={`flex items-center justify-center px-3 py-3 rounded-2xl border transition ${fetchTable ? 'bg-green-100 border-green-400 text-green-700' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
          title="Toggle table output"
          style={{ minWidth: 48, minHeight: 48 }}
          onClick={() => setFetchTable(v => !v)}
        >
          <FileDown size={20} />
        </button>
        <button type="submit" disabled={loading || !input.trim()} className="bg-blue-600 hover:bg-blue-700 text-white px-7 py-3 rounded-2xl shadow font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed text-base flex items-center gap-2">
          <Send size={20} />
        </button>
      </form>
    </div>
  );
}

export default App;
