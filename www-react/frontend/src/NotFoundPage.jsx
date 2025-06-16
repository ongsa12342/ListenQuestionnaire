import React from 'react';
import { Box, Button, Container, Typography } from '@mui/material';
import { Link } from 'react-router-dom';

function NotFoundPage() {
    return (
        <Container maxWidth="sm" sx={{ textAlign: 'center', mt: 8 }}>
            <Box>
                <Typography variant="h1" component="h1" gutterBottom>
                    404
                </Typography>
                <Typography variant="h5" component="h2" gutterBottom>
                    Page Not Found
                </Typography>
                <Typography variant="body1" sx={{ mb: 4 }}>
                    The page you are looking for does not exist.
                </Typography>
                <Button component={Link} to="/" variant="contained" color="primary">
                    Go to Homepage
                </Button>
            </Box>
        </Container>
    );
}

export default NotFoundPage; 