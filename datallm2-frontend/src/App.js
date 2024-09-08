import React, { useState } from 'react';
import axios from 'axios';
import DOMPurify from 'dompurify';
import { 
  ThemeProvider, createTheme, 
  CssBaseline, AppBar, Toolbar, Typography, 
  Container, Paper, TextField, Button, 
  List, ListItem, ListItemText, ListItemAvatar, 
  Avatar, CircularProgress, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import { Send as SendIcon, Person as PersonIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import SmartToyIcon from '@mui/icons-material/SmartToy';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/query', 
        { query: userMessage },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      setMessages(prev => [
        ...prev, 
        { type: 'bot', content: response.data.steps, isSteps: true },
        { type: 'bot', content: response.data.friendlyResponse }
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { type: 'bot', content: 'Sorry, an error occurred.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const createMarkup = (html) => {
    return {__html: DOMPurify.sanitize(html)};
  }

  const renderSteps = (steps) => (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography>Query Process Steps</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="h6">1. Relevant Tables</Typography>
        <Typography>{steps.relevant_tables.join(', ')}</Typography>

        <Typography variant="h6">2. Query Intent</Typography>
        <Typography>{steps.query_intent}</Typography>

        <Typography variant="h6">3. Generated SQL</Typography>
        <pre>{steps.generated_sql}</pre>

        <Typography variant="h6">4. SQL Validation</Typography>
        <Typography>{steps.sql_validated ? 'Successful' : 'Failed'}</Typography>

        <Typography variant="h6">5. Query Result</Typography>
        {steps.error ? (
          <Typography color="error">{steps.error}</Typography>
        ) : (
          <pre>{JSON.stringify(steps.query_result, null, 2)}</pre>
        )}
      </AccordionDetails>
    </Accordion>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">
            Enterprise Data Assistant
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 140px)' }}>
          <List sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
            {messages.map((message, index) => (
              <ListItem key={index} alignItems="flex-start" sx={{ flexDirection: message.type === 'user' ? 'row-reverse' : 'row' }}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: message.type === 'user' ? 'primary.main' : 'secondary.main' }}>
                    {message.type === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                  </Avatar>
                </ListItemAvatar>
                <Paper 
                  elevation={1} 
                  sx={{ 
                    p: 2, 
                    maxWidth: '70%', 
                    bgcolor: message.type === 'user' ? 'primary.light' : 'secondary.light',
                    color: message.type === 'user' ? 'primary.contrastText' : 'secondary.contrastText'
                  }}
                >
                  {message.type === 'user' ? (
                    <ListItemText primary={message.content} />
                  ) : message.isSteps ? (
                    renderSteps(message.content)
                  ) : (
                    <div dangerouslySetInnerHTML={createMarkup(message.content)} />
                  )}
                </Paper>
              </ListItem>
            ))}
          </List>
          <form onSubmit={handleSubmit} style={{ display: 'flex' }}>
            <TextField
              fullWidth
              variant="outlined"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your query here..."
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              variant="contained" 
              color="primary" 
              endIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              disabled={isLoading}
              sx={{ ml: 1 }}
            >
              Send
            </Button>
          </form>
        </Paper>
      </Container>
    </ThemeProvider>
  );
}

export default App;