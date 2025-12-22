# Frontend Master Plan: AI Tutor & RAG Chat Service

> [!IMPORT] Backend API Reference
> All API calls should be prefixed with `/api/v1`.
> **Authentication**: Managed via Supabase Auth (JWT).
> **Authorization**: `Bearer <token>` header required for all endpoints.

## 0. Tech Stack & Prerequisites

- **Framework**: React 18+ (Vite).
- **Language**: TypeScript.
- **Styling**: Vanilla CSS.
- **Data Fetching**: `tanstack/react-query` (recommended).
- **Auth**: `@supabase/supabase-js`.

---

## 1. Authentication & Onboarding

**Goal**: Simple, frictionless entry.

- [ ] **Login Screen** (`/login`)

  - **API**: `supabase.auth.signInWithPassword({ email, password })`
  - **Form**: Email (`type="email"`), Password (`type="password"`).
  - **Links**: "Forget Password?", "Register".
  - **Error Handling**: Catch Supabase `AuthApiError`.

- [ ] **Registration Screen** (`/register`)
  - **API**: `POST /users` (Calls `auth_api.create_user` which wraps Supabase `signUp`)
  - **Form**: Full Name, Email, Password, Confirm Password.
  - **Validation**:
    - Password strength (client-side regex).
    - Match password confirmation.

## 2. Core App Shell

**Goal**: Persistent navigation and role-based access.

- [ ] **Sidebar Component**
  - **State**: Fetch current user profile from `supabase.auth.getUser()`.
  - **Role Check**: If `user_metadata.role === 'admin'`, show Admin Nav.
  - **Chat History**:
    - **API**: `GET /sessions?limit=20`
    - **Function**: List recent chats. On click -> navigate to `/chat/:sessionId`.

## 3. Student Interface: Smart Chat (`/chat`)

**Goal**: The primary learning interface.

- [ ] **Empty State (New Chat)**

  - **API**: `GET /bots` (to get default bot_id).
  - **Hero Text**: "How can I help you study today?"
  - **Suggestions**: Static list or fetched from a config.

- [ ] **Chat Session Logic**

  - **API (Create/Send)**: `POST /bots/{bot_id}/ask`
    - Body: `{ message: "Hello", streaming: true }`
  - **API (Continue)**: `POST /bots/{bot_id}/ask/{session_id}`
  - **Streaming**: Handle `text/event-stream`. Accumulate `data.response` chunks.
  - **Citations**: Parse response for citations (e.g., `[JSON reference]`) and render as interactive elements.

- [ ] **Citations Sidebar**
  - **Trigger**: User clicks a citation bubble `[1]`.
  - **Content**: Display the `page_content` from the citation metadata returned in the chat response.
  - **Link**: "View Source" button links to `/library/doc/:docId`.

## 4. Student Library (`/library`)

**Description**: A **Read-Only** explorer for the knowledge base. Since students cannot upload, this view allows them to browse the documents that Instructors have curated (e.g., Syllabi, Textbooks, Lectures).
**Mechanism**: It fetches the list of "Knowledge Bases" (Subject folders) and then lists the documents inside them.

- [ ] **Knowledge Base List**

  - **API**: `GET /knowledge_bases`
  - **UI**: Grid of folders (e.g., "CS101", "History 202").
  - **Details**: Name, Description, Document Count (`document_count`).

- [ ] **Document Browser (Drill-down)**
  - **API**: `GET /knowledge_bases/{kb_id}`
  - **UI**: Table of documents within the selected KB.
  - **Columns**: Filename, File Type, Size, Added Date.
  - **Action**: "Chat with this" -> Navigates to `/chat` with a system prompt context to focus on this document (if supported) or just generic chat.

## 5. Instructor Portal (Admin Only) (`/instructor`)

**Description**: The control center. Since we lack a dedicated "Analytics" API in the backend, we will simply query the Supabase tables directly (which is safe for Admins) to generate the dashboard stats.

- [ ] **Dashboard (`/instructor/dashboard`)**

  - **Mechanism**: Use backend API `GET /api/v1/analytics/summary` (Admin/Instructor Only).
  - **Response Structure**:
    ```json
    {
    	"total_students": 123,
    	"total_chats": 456,
    	"total_kbs": 12
    }
    ```
  - **Recent Users**: `GET /users` (limit 5).

- [ ] **Knowledge Manager (`/instructor/knowledge`)**

  - **List KBs**: `GET /knowledge_bases` (Same as student, but with Edit buttons).
  - **Create KB**: `POST /knowledge_bases` (Name, Description).
  - **Edit/Delete KB**: `PATCH /knowledge_bases/{id}`, `DELETE /knowledge_bases/{id}`.

- [ ] **Bot Manager (`/instructor/bots`)**

  - **API**: `GET /bots`
  - **Config**: `PATCH /bots/{bot_id}/config`
    - Update **System Prompt** ("You are a strict physics tutor...").
    - Update **Temperature** (0.1 - 1.0).
  - **Create Bot**: `POST /bots` (Name, Description).

- [ ] **User Management**
  - **API**: `GET /users`
  - **Actions**:
    - List all registered users.
    - Delete User: `DELETE /users/{user_id}`.

## 6. General Components

- [ ] **Loading Skeleton**: Use while `isLoading` from API hooks.
- [ ] **Toast Notifications**: On API 200/400/500 responses.

---
