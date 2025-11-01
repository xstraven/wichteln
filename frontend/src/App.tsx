import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import CreateGroup from "./pages/CreateGroup";
import Reveal from "./pages/Reveal";

const App = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create" element={<CreateGroup />} />
          <Route path="/reveal" element={<Reveal />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

export default App;
