/** Secret admin dashboard base path, e.g. "/suqilic-control". Must match the backend's ADMIN_URL_PATH. */
export const ADMIN_PATH = `/${(import.meta.env.VITE_ADMIN_PATH ?? 'suqilic-control').replace(/^\/|\/$/g, '')}`
