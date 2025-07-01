import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
//import './index.css'
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from './App.jsx'
import Qkd from './Qkd.jsx'
import Network from './Network.jsx';


const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "qkd",
    element: <Network />,
  },
]);

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);