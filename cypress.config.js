const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:8000',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    video: true,
    videosFolder: 'cypress/videos',
    screenshot: true,
    screenshotsFolder: 'cypress/screenshots',
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    setupNodeEvents(on, config) {
      // Take screenshots on test completion
      on('after:screenshot', (details) => {
        console.log('Screenshot taken:', details.path)
      })
      
      // Video processing
      on('after:spec', (spec, results) => {
        if (results && results.video) {
          console.log('Video recorded:', results.video)
        }
      })
    },
  },
})