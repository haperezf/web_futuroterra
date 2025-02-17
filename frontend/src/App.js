import React, { useState } from 'react';
import axios from 'axios';

const App = () => {
  const [message, setMessage] = useState('');
  const [responseMsg, setResponseMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (message.trim() === '') return;
    setIsLoading(true);
    try {
      // The backend is available at http://backend:8000 because of Docker Compose networking.
      const res = await axios.post('http://localhost:8000/api/chat', { message });
      setResponseMsg(res.data.response);
    } catch (error) {
      console.error('Error sending message:', error);
      setResponseMsg('Ocurrió un error al comunicarse con el servidor.');
    }
    setIsLoading(false);
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <img src="Futuroterra_logo.png" alt="Logo de FuturoTerra" style={styles.logo} />
        <h1 style={styles.headerTitle}>FuturoTerra Chatbot</h1>
        <p style={styles.headerSubtitle}>Caminos hacia la Sustentabilidad</p>
      </header>
      <main style={styles.main}>
        <div style={styles.chatContainer}>
          <h2 style={styles.title}>Interfaz del Chatbot</h2>
          <div style={styles.inputContainer}>
            <input
              type="text"
              placeholder="Escribe tu mensaje..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              style={styles.input}
            />
            <button onClick={handleSend} style={styles.button} disabled={isLoading}>
              {isLoading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
          {responseMsg && (
            <div style={styles.responseContainer}>
              <p style={styles.responseText}>{responseMsg}</p>
            </div>
          )}
        </div>
      </main>
      <footer style={styles.footer}>
        <p>&copy; 2024 FuturoTerra. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
};

const styles = {
  container: {
    fontFamily: 'Arial, sans-serif',
    backgroundColor: '#f4f4f9',
    color: '#333',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    backgroundColor: '#4caf50',
    color: 'white',
    textAlign: 'center',
    padding: '20px 0',
  },
  logo: {
    maxWidth: '150px',
    margin: '10px 0',
  },
  headerTitle: {
    fontSize: '2.5em',
    margin: 0,
  },
  headerSubtitle: {
    fontSize: '1.2em',
    margin: 0,
  },
  main: {
    flex: 1,
    padding: '20px',
    maxWidth: '800px',
    margin: 'auto',
  },
  chatContainer: {
    background: '#fff',
    padding: '40px',
    borderRadius: '10px',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  title: {
    color: '#4caf50',
    fontSize: '2em',
    borderBottom: '2px solid #4caf50',
    paddingBottom: '10px',
    marginBottom: '20px',
  },
  inputContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '20px',
  },
  input: {
    flex: 1,
    padding: '10px',
    fontSize: '1rem',
    border: '1px solid #ccc',
    borderRadius: '5px',
    marginRight: '10px',
  },
  button: {
    padding: '10px 20px',
    fontSize: '1rem',
    border: 'none',
    borderRadius: '5px',
    backgroundColor: '#4caf50',
    color: '#fff',
    cursor: 'pointer',
  },
  responseContainer: {
    backgroundColor: '#e8f5e9',
    borderLeft: '5px solid #4caf50',
    padding: '20px',
    borderRadius: '5px',
  },
  responseText: {
    fontSize: '1.2rem',
  },
  footer: {
    backgroundColor: '#333',
    color: 'white',
    textAlign: 'center',
    padding: '10px 0',
  },
};

export default App;
