import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Heart, MessageCircle, Send, Bookmark, Home, Search, PlusSquare, User, X,
  Sparkles, LogOut, Inbox, Bell,
} from "lucide-react";

// Point this at your deployed Render API URL once you've deployed the backend.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const AVATAR_GRADIENTS = [
  "linear-gradient(135deg,#F5C84C,#FF4FA3)",
  "linear-gradient(135deg,#7C5CFF,#FF4FA3)",
  "linear-gradient(135deg,#33D6C0,#7C5CFF)",
  "linear-gradient(135deg,#FF8A4C,#F5C84C)",
  "linear-gradient(135deg,#4CC9FF,#7C5CFF)",
];
const gradientFor = (id) => AVATAR_GRADIENTS[Math.abs(hashCode(id || "")) % AVATAR_GRADIENTS.length];
function hashCode(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i); return h; }

// ---------- API client ----------
function useApi(token, setToken) {
  const request = useCallback(async (path, opts = {}) => {
    const headers = { ...(opts.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${API_BASE_URL}${path}`, { ...opts, headers });
    if (res.status === 401) { setToken(null); throw new Error("Session expired — please log in again"); }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }
    if (res.status === 204) return null;
    return res.json();
  }, [token, setToken]);
  return request;
}

function Avatar({ userId, url, size = 40, ring = false }) {
  return (
    <div style={{ width: size, height: size, borderRadius: "50%", padding: ring ? 2.5 : 0,
      background: ring ? "linear-gradient(135deg,#F5C84C,#FF4FA3)" : "transparent", flexShrink: 0 }}>
      {url ? (
        <img src={url} alt="" style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover", border: "2px solid #0E0B1A" }} />
      ) : (
        <div style={{ width: "100%", height: "100%", borderRadius: "50%", background: gradientFor(userId), border: "2px solid #0E0B1A" }} />
      )}
    </div>
  );
}

// ---------- Auth screen ----------
function AuthScreen({ onLogin, onSignup, error, busy }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  const submit = () => (mode === "login" ? onLogin(form.email, form.password) : onSignup(form));

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 340 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center", marginBottom: 28 }}>
          <Sparkles size={26} color="#F5C84C" />
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 24 }}>Nova World</span>
        </div>

        {mode === "signup" && (
          <input placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} style={inputStyle} />
        )}
        <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={inputStyle} />
        <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={inputStyle} />

        {error && <div style={{ color: "#FF4FA3", fontSize: 13, marginBottom: 10 }}>{error}</div>}

        <button onClick={submit} disabled={busy} style={{ width: "100%", background: "linear-gradient(135deg,#F5C84C,#FF4FA3)", border: "none", borderRadius: 10, padding: "12px 0", color: "#0E0B1A", fontWeight: 700, fontSize: 14, cursor: "pointer", marginTop: 4 }}>
          {busy ? "…" : mode === "login" ? "Log in" : "Sign up"}
        </button>

        <button onClick={() => setMode(mode === "login" ? "signup" : "login")} style={{ width: "100%", background: "none", border: "none", color: "#8B85A0", fontSize: 13, marginTop: 14, cursor: "pointer" }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
        </button>
      </div>
    </div>
  );
}
const inputStyle = { width: "100%", background: "#171227", border: "1px solid #241d38", borderRadius: 10, padding: "11px 14px", color: "#F2EEFA", fontSize: 14, outline: "none", marginBottom: 10, boxSizing: "border-box" };

// ---------- Stories ----------
function StoriesBar({ stories, currentUser, onOpen, onUpload }) {
  const fileRef = useRef(null);
  const byAuthor = {};
  stories.forEach((s) => { (byAuthor[s.author_id] = byAuthor[s.author_id] || []).push(s); });

  return (
    <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 20, marginBottom: 6 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, flexShrink: 0 }}>
        <button onClick={() => fileRef.current?.click()} style={{ width: 58, height: 58, borderRadius: "50%", border: "1.5px dashed #8B85A0", background: "none", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
          <PlusSquare size={20} color="#8B85A0" />
        </button>
        <input ref={fileRef} type="file" accept="image/*,video/*" style={{ display: "none" }} onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])} />
        <span style={{ fontSize: 11, color: "#8B85A0" }}>Your story</span>
      </div>
      {Object.entries(byAuthor).map(([authorId, group]) => (
        <div key={authorId} onClick={() => onOpen(group)} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, flexShrink: 0, cursor: "pointer" }}>
          <Avatar userId={authorId} size={58} ring={!group.every((s) => s.viewed_by_me)} />
          <span style={{ fontSize: 11, color: "#8B85A0", maxWidth: 60, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {authorId === currentUser?.id ? "You" : authorId.slice(0, 6)}
          </span>
        </div>
      ))}
    </div>
  );
}

function StoryViewer({ group, onClose, onView }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => { if (group?.[idx]) onView(group[idx].id); }, [idx, group]); // eslint-disable-line
  if (!group) return null;
  const story = group[idx];
  const next = () => (idx < group.length - 1 ? setIdx(idx + 1) : onClose());
  const prev = () => idx > 0 && setIdx(idx - 1);

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000", zIndex: 60, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", gap: 4, padding: "10px 12px" }}>
        {group.map((_, i) => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i <= idx ? "#F5C84C" : "rgba(255,255,255,0.25)" }} />
        ))}
      </div>
      <div style={{ position: "absolute", top: 20, right: 14 }}>
        <button className="icon-btn" onClick={onClose}><X size={22} color="#fff" /></button>
      </div>
      <div style={{ flex: 1, display: "flex" }}>
        <div onClick={prev} style={{ width: "35%" }} />
        {story.media_type === "video" ? (
          <video src={story.media_url} autoPlay style={{ flex: 1, objectFit: "contain" }} onEnded={next} />
        ) : (
          <img src={story.media_url} alt="" style={{ flex: 1, objectFit: "contain" }} />
        )}
        <div onClick={next} style={{ width: "35%" }} />
      </div>
    </div>
  );
}

// ---------- Feed / Post ----------
function Post({ post, onLike, onSave, onOpenComments }) {
  return (
    <article style={{ marginBottom: 28, borderBottom: "1px solid #241d38", paddingBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "2px 4px 10px" }}>
        <Avatar userId={post.author_id} size={34} ring />
        <span style={{ fontSize: 14, fontWeight: 600 }}>{post.author_id.slice(0, 8)}</span>
      </div>
      <div style={{ width: "100%", aspectRatio: "4/5", borderRadius: 14, overflow: "hidden", background: gradientFor(post.id) }}
           onDoubleClick={() => !post.liked_by_me && onLike(post.id)}>
        {post.media_type === "video" ? (
          <video src={post.media_url} controls style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <img src={post.media_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        )}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", padding: "12px 4px 6px" }}>
        <div style={{ display: "flex", gap: 16 }}>
          <button className="icon-btn" onClick={() => onLike(post.id)}>
            <Heart size={24} color={post.liked_by_me ? "#FF4FA3" : "#F2EEFA"} fill={post.liked_by_me ? "#FF4FA3" : "none"} strokeWidth={1.8} />
          </button>
          <button className="icon-btn" onClick={() => onOpenComments(post)}><MessageCircle size={24} strokeWidth={1.8} /></button>
          <button className="icon-btn"><Send size={22} strokeWidth={1.8} /></button>
        </div>
        <button className="icon-btn" onClick={() => onSave(post.id)}><Bookmark size={22} strokeWidth={1.8} /></button>
      </div>
      <div style={{ padding: "0 4px" }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>{post.like_count} likes</span>
        <p style={{ fontSize: 14, margin: "4px 0 0" }}><span style={{ fontWeight: 600 }}>{post.author_id.slice(0, 8)}</span> {post.caption}</p>
        {post.comment_count > 0 && (
          <button onClick={() => onOpenComments(post)} style={{ background: "none", border: "none", padding: 0, marginTop: 4, cursor: "pointer" }}>
            <span style={{ fontSize: 13, color: "#8B85A0" }}>View all {post.comment_count} comments</span>
          </button>
        )}
      </div>
    </article>
  );
}

function CommentsSheet({ post, comments, onClose, onAdd }) {
  const [text, setText] = useState("");
  if (!post) return null;
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(14,11,26,0.7)", backdropFilter: "blur(4px)", zIndex: 50, display: "flex", alignItems: "flex-end", justifyContent: "center" }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "#171227", width: "100%", maxWidth: 470, borderRadius: "20px 20px 0 0", maxHeight: "70vh", display: "flex", flexDirection: "column", border: "1px solid #241d38" }}>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "16px 18px", borderBottom: "1px solid #241d38" }}>
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600 }}>Comments</span>
          <button className="icon-btn" onClick={onClose}><X size={20} color="#8B85A0" /></button>
        </div>
        <div style={{ overflowY: "auto", padding: "14px 18px", flex: 1 }}>
          {(comments || []).map((c) => (
            <div key={c.id} style={{ display: "flex", gap: 10, marginBottom: 14 }}>
              <Avatar userId={c.user_id} size={30} />
              <p style={{ fontSize: 14, margin: 0 }}><span style={{ fontWeight: 600 }}>{c.user_id.slice(0, 8)}</span> {c.text}</p>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 10, padding: 14, borderTop: "1px solid #241d38" }}>
          <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && text.trim() && (onAdd(post.id, text.trim()), setText(""))}
                 placeholder="Add a comment…" style={{ flex: 1, background: "#0E0B1A", border: "1px solid #241d38", borderRadius: 20, padding: "10px 14px", color: "#F2EEFA", fontSize: 14, outline: "none" }} />
          <button onClick={() => { if (text.trim()) { onAdd(post.id, text.trim()); setText(""); } }} style={{ background: "none", border: "none", color: "#F5C84C", fontWeight: 600, cursor: "pointer" }}>Post</button>
        </div>
      </div>
    </div>
  );
}

// ---------- DMs ----------
function DMsView({ threads, activeThread, messages, onOpenThread, onSend, currentUser }) {
  const [text, setText] = useState("");
  if (activeThread) {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 130px)" }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "10px 4px" }}>
          {messages.map((m) => (
            <div key={m.id} style={{ display: "flex", justifyContent: m.sender_id === currentUser.id ? "flex-end" : "flex-start", marginBottom: 8 }}>
              <div style={{ maxWidth: "75%", background: m.sender_id === currentUser.id ? "linear-gradient(135deg,#7C5CFF,#FF4FA3)" : "#171227", padding: "9px 13px", borderRadius: 16, fontSize: 14 }}>
                {m.text}
              </div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 10, padding: "10px 4px" }}>
          <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && text.trim() && (onSend(text.trim()), setText(""))}
                 placeholder="Message…" style={{ flex: 1, background: "#171227", border: "1px solid #241d38", borderRadius: 20, padding: "10px 14px", color: "#F2EEFA", fontSize: 14, outline: "none" }} />
          <button onClick={() => { if (text.trim()) { onSend(text.trim()); setText(""); } }} className="icon-btn"><Send size={20} color="#F5C84C" /></button>
        </div>
      </div>
    );
  }
  return (
    <div>
      {threads.length === 0 && <p style={{ color: "#8B85A0", fontSize: 14, padding: "20px 4px" }}>No conversations yet.</p>}
      {threads.map((t) => (
        <div key={t.username} onClick={() => onOpenThread(t.username)} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 4px", borderBottom: "1px solid #1c1730", cursor: "pointer" }}>
          <Avatar userId={t.username} url={t.avatar_url} size={46} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{t.display_name || t.username}</div>
            <div style={{ color: "#8B85A0", fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.last_message}</div>
          </div>
          {t.unread && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#F5C84C" }} />}
        </div>
      ))}
    </div>
  );
}

// ---------- Main app ----------
export default function NovaWorld() {
  const [token, setToken] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  const api = useApi(token, setToken);

  const [tab, setTab] = useState("feed");
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState({});
  const [activeComments, setActiveComments] = useState(null);
  const [stories, setStories] = useState([]);
  const [activeStoryGroup, setActiveStoryGroup] = useState(null);
  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [thread_messages, setThreadMessages] = useState([]);
  const [globalError, setGlobalError] = useState("");

  const loadFeed = useCallback(async () => {
    try { setPosts(await api("/posts/feed")); } catch (e) { setGlobalError(e.message); }
  }, [api]);
  const loadStories = useCallback(async () => {
    try { setStories(await api("/stories/feed")); } catch (e) { /* non-fatal */ }
  }, [api]);
  const loadThreads = useCallback(async () => {
    try { setThreads(await api("/messages/threads")); } catch (e) { /* non-fatal */ }
  }, [api]);

  useEffect(() => {
    if (!token) return;
    api("/users/me").then(setCurrentUser).catch(() => setToken(null));
    loadFeed(); loadStories(); loadThreads();
  }, [token]); // eslint-disable-line

  const doLogin = async (email, password) => {
    setAuthBusy(true); setAuthError("");
    try {
      const tok = await api("/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
      setToken(tok.access_token);
    } catch (e) { setAuthError(e.message); } finally { setAuthBusy(false); }
  };
  const doSignup = async (form) => {
    setAuthBusy(true); setAuthError("");
    try {
      await api("/auth/signup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      await doLogin(form.email, form.password);
    } catch (e) { setAuthError(e.message); } finally { setAuthBusy(false); }
  };

  const toggleLike = async (id) => {
    const post = posts.find((p) => p.id === id);
    setPosts((ps) => ps.map((p) => p.id === id ? { ...p, liked_by_me: !p.liked_by_me, like_count: p.like_count + (p.liked_by_me ? -1 : 1) } : p));
    try { await api(`/posts/${id}/like`, { method: post.liked_by_me ? "DELETE" : "POST" }); } catch (e) { setGlobalError(e.message); }
  };
  const openComments = async (post) => {
    setActiveComments(post);
    try { setComments((c) => ({ ...c, [post.id]: null })); const list = await api(`/posts/${post.id}/comments`); setComments((c) => ({ ...c, [post.id]: list })); } catch (e) { setGlobalError(e.message); }
  };
  const addComment = async (postId, text) => {
    try {
      const c = await api(`/posts/${postId}/comments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      setComments((prev) => ({ ...prev, [postId]: [...(prev[postId] || []), c] }));
      setPosts((ps) => ps.map((p) => p.id === postId ? { ...p, comment_count: p.comment_count + 1 } : p));
    } catch (e) { setGlobalError(e.message); }
  };

  const uploadStory = async (file) => {
    const fd = new FormData(); fd.append("file", file);
    try { await api("/stories", { method: "POST", body: fd }); loadStories(); } catch (e) { setGlobalError(e.message); }
  };
  const viewStory = async (storyId) => { try { await api(`/stories/${storyId}/view`, { method: "POST" }); } catch (e) { /* non-fatal */ } };

  const openThread = async (username) => {
    setActiveThread(username);
    try { setThreadMessages(await api(`/messages/${username}`)); } catch (e) { setGlobalError(e.message); }
  };
  const sendMessage = async (text) => {
    try {
      const m = await api(`/messages/${activeThread}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      setThreadMessages((ms) => [...ms, m]);
    } catch (e) { setGlobalError(e.message); }
  };

  if (!token) {
    return (
      <div style={{ minHeight: "100vh", background: "#0E0B1A", color: "#F2EEFA", fontFamily: "'Inter', sans-serif" }}>
        <style>{`@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&display=swap');`}</style>
        <AuthScreen onLogin={doLogin} onSignup={doSignup} error={authError} busy={authBusy} />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#0E0B1A", fontFamily: "'Inter', sans-serif", color: "#F2EEFA" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
        .icon-btn { background: none; border: none; cursor: pointer; padding: 2px; display: flex; }
      `}</style>

      <header style={{ position: "sticky", top: 0, zIndex: 10, background: "rgba(14,11,26,0.9)", backdropFilter: "blur(8px)", borderBottom: "1px solid #241d38", padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Sparkles size={20} color="#F5C84C" />
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 19 }}>Nova World</span>
        </div>
        <button className="icon-btn" onClick={() => setToken(null)}><LogOut size={19} color="#8B85A0" /></button>
      </header>

      {globalError && <div style={{ background: "rgba(255,79,163,0.1)", color: "#FF4FA3", padding: "8px 18px", fontSize: 13 }}>{globalError}</div>}

      <main style={{ maxWidth: 470, margin: "0 auto", padding: "18px 14px 90px" }}>
        {tab === "feed" && (
          <>
            <StoriesBar stories={stories} currentUser={currentUser} onUpload={uploadStory}
                        onOpen={(group) => setActiveStoryGroup(group)} />
            {posts.length === 0 && <p style={{ color: "#8B85A0", fontSize: 14 }}>No posts yet — follow people or check Explore.</p>}
            {posts.map((post) => (
              <Post key={post.id} post={post} onLike={toggleLike} onSave={() => {}} onOpenComments={openComments} />
            ))}
          </>
        )}
        {tab === "dms" && (
          <DMsView threads={threads} activeThread={activeThread} messages={thread_messages}
                   onOpenThread={openThread} onSend={sendMessage} currentUser={currentUser} />
        )}
        {tab === "profile" && currentUser && (
          <div style={{ padding: "24px 4px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <Avatar userId={currentUser.id} url={currentUser.avatar_url} size={84} ring />
              <div>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 17 }}>{currentUser.username}</div>
                <div style={{ color: "#8B85A0", fontSize: 13, marginTop: 4 }}>{currentUser.bio || "No bio yet"}</div>
              </div>
            </div>
          </div>
        )}
      </main>

      <nav style={{ position: "fixed", bottom: 0, left: 0, right: 0, background: "rgba(14,11,26,0.95)", backdropFilter: "blur(8px)", borderTop: "1px solid #241d38", display: "flex", justifyContent: "space-around", padding: "12px 0 16px" }}>
        <button className="icon-btn" onClick={() => { setTab("feed"); setActiveThread(null); }}><Home size={24} color={tab === "feed" ? "#F5C84C" : "#8B85A0"} strokeWidth={1.8} /></button>
        <button className="icon-btn"><Search size={24} color="#8B85A0" strokeWidth={1.8} /></button>
        <button className="icon-btn" onClick={() => { setTab("dms"); loadThreads(); }}><Inbox size={24} color={tab === "dms" ? "#F5C84C" : "#8B85A0"} strokeWidth={1.8} /></button>
        <button className="icon-btn"><Bell size={24} color="#8B85A0" strokeWidth={1.8} /></button>
        <button className="icon-btn" onClick={() => setTab("profile")}>
          <div style={{ borderRadius: "50%", border: tab === "profile" ? "2px solid #F5C84C" : "2px solid transparent" }}>
            <Avatar userId={currentUser?.id} url={currentUser?.avatar_url} size={22} />
          </div>
        </button>
      </nav>

      <CommentsSheet post={activeComments} comments={activeComments ? comments[activeComments.id] : null}
                     onClose={() => setActiveComments(null)} onAdd={addComment} />
      <StoryViewer group={activeStoryGroup} onClose={() => setActiveStoryGroup(null)} onView={viewStory} />
    </div>
  );
}
