const express = require('express');
const app = express();
const path = require('path');
const fs = require('fs');

// Helper function to determine recommendation based on percentage changes
function getRecommendation(change5, change10) {
    if (change5 > 1.5 && change10 > 3) {
        return "BUY";
    } else if (change5 < -1.5 && change10 < -3) {
        return "SELL";
    } else {
        return "HOLD";
    }
}

// Handling GET request for stock predictions
app.get('/prediction/:stock', (req, res) => {
    const stock = req.params.stock.toUpperCase();

    // Define the path to the prediction file
    const predictionFile = path.join(__dirname, 'output', `${stock}.json`);

    // Read the existing prediction file
    fs.readFile(predictionFile, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading file:', err);
            return res.status(500).json({ error: 'Failed to read prediction data' });
        }

        // Parse the JSON data
        let predictionData;
        try {
            predictionData = JSON.parse(data);
        } catch (err) {
            console.error('Error parsing JSON:', err);
            return res.status(500).json({ error: 'Failed to parse prediction data' });
        }

        // Extract the first three values from the prediction data
        const { predicted_close, change_5_days, change_10_days } = predictionData;

        // Calculate the advice based on 5-day and 10-day changes
        const advice = getRecommendation(change_5_days, change_10_days);

        // Add the recommendation to the prediction data
        predictionData.advice = advice;

        // Write the updated prediction data back to the file
        fs.writeFile(predictionFile, JSON.stringify(predictionData, null, 2), (err) => {
            if (err) {
                console.error('Error writing file:', err);
                return res.status(500).json({ error: 'Failed to save updated prediction data' });
            }

            // Send the updated prediction data as a response
            res.json(predictionData);
        });
    });
});

// Serve the frontend HTML
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'interface.html'));
});

app.listen(3000, () => {
    console.log("Server running on http://localhost:3000");
});
