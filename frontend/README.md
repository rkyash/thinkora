# Thinkora Frontend

This directory contains the user interface for Thinkora, built with [React 19](https://react.dev/), [Vite](https://vitejs.dev/), and [TypeScript](https://www.typescriptlang.org/). It provides a responsive, modern interface for managing workspaces, notebooks, chatting with documents, and exploring knowledge graphs.

## Technology Stack

* **Framework**: React 19 + Vite
* **Language**: TypeScript
* **Styling**: Tailwind CSS v3 + [shadcn/ui](https://ui.shadcn.com/)
* **State Management**: [Zustand](https://zustand-demo.pmnd.rs/) (global state)
* **Data Fetching**: [TanStack Query v5](https://tanstack.com/query/latest) (server state caching/syncing)
* **Routing**: React Router v7
* **Animations**: Framer Motion
* **Graph Visualization**: [@xyflow/react](https://reactflow.dev/) (React Flow)
* **Rich Text Editor**: [TipTap](https://tiptap.dev/)

## Project Structure

```
frontend/
├── src/
│   ├── api/          # Axios instances, API client service methods
│   ├── components/   # UI components
│   │   ├── ui/       # Generic/shadcn UI components
│   │   └── ...       # Feature-specific components
│   ├── hooks/        # Custom React hooks
│   ├── lib/          # Utilities (e.g., utils.ts for Tailwind merging)
│   ├── pages/        # Route pages/views
│   ├── stores/       # Zustand stores for global state
│   ├── styles/       # Global CSS styles (Tailwind imports)
│   ├── types/        # TypeScript interfaces and types
│   ├── App.tsx       # Root component and routing setup
│   └── main.tsx      # Application entry point
├── public/           # Static assets
├── index.html        # HTML template
├── package.json      # Dependencies and scripts
├── vite.config.ts    # Vite configuration
├── tsconfig.json     # TypeScript configuration
└── tailwind.config.js# Tailwind CSS configuration
```

## Setup Instructions

1. **Install Dependencies**:
   Ensure you have [Node.js](https://nodejs.org/) installed, then run:
   ```bash
   npm install
   ```

2. **Environment Variables**:
   Create a `.env` file (or `.env.local`) based on the required variables. Key variables include:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1  # Points to the local backend during development
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```
   The application will typically be available at `http://localhost:5173`.

## Available Scripts

* `npm run dev`: Starts the development server with Hot Module Replacement (HMR).
* `npm run build`: Compiles TypeScript and builds the application for production.
* `npm run preview`: Locally previews the production build.
* `npm run lint`: Runs ESLint to check code quality.

## Key Patterns

* **Data Fetching**: All API calls are encapsulated in the `src/api/` directory using Axios. React components interact with these calls via custom hooks utilizing TanStack Query (`useQuery`, `useMutation`), ensuring efficient caching, retries, and background updates.
* **State Management**: Local UI state uses standard React hooks (`useState`, `useReducer`). Global state (e.g., current workspace, user preferences) is managed via simple Zustand stores in `src/stores/`.
* **Styling**: Tailwind CSS utility classes are used exclusively. Complex class logic is handled via `clsx` and `tailwind-merge` in `src/lib/utils.ts`.

## Documentation

For full project documentation, see the [main documentation](../README.md).
