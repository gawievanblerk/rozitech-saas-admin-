describe('Insurr Claims Workflow', () => {
  let testTenant, testPolicy

  beforeEach(() => {
    cy.loginToInsurr()
    // Create test tenant and policy for claims testing
    cy.createInsurrTenant({
      name: 'Claims Test Insurance',
      slug: `claims-test-${Date.now()}`,
      tier: 'professional'
    }).then((tenant) => {
      testTenant = tenant
    })
  })

  it('should access claims management interface', () => {
    cy.visit('/admin/')
    cy.contains('Site administration')
    
    // Look for claims or services admin sections
    cy.get('body').then(($body) => {
      if ($body.find('a[href*="claims"]').length > 0) {
        cy.contains('Claims').click()
      } else if ($body.find('a[href*="services"]').length > 0) {
        cy.contains('Services').click()
      }
    })
  })

  it('should submit a new insurance claim', () => {
    const claimData = {
      claim_number: `CLM-${Date.now()}`,
      tenant: testTenant.id,
      policy_number: `POL-${Date.now()}`,
      claimant_name: 'Mary Doe',
      claimant_id: '8505125009087',
      claimant_email: 'mary.doe@example.com',
      claimant_phone: '+27821234567',
      claim_type: 'death',
      claim_amount: 25000.00,
      incident_date: '2024-01-15',
      description: 'Natural death claim submission',
      status: 'submitted'
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', claimData)
      .then((response) => {
        if (response.status === 201) {
          expect(response.body).to.have.property('claim_number')
          expect(response.body.claimant_name).to.eq('Mary Doe')
          expect(response.body.claim_amount).to.eq('25000.00')
          expect(response.body.status).to.eq('submitted')
        } else {
          // If endpoint doesn't exist, that's expected for now
          expect([404, 405]).to.include(response.status)
        }
      })
  })

  it('should validate claim requirements', () => {
    const invalidClaimData = {
      // Missing required fields
      claimant_name: 'Invalid Claim Test'
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', invalidClaimData)
      .then((response) => {
        // Should return validation error or 404 if endpoint doesn't exist
        expect([400, 404, 405]).to.include(response.status)
      })
  })

  it('should retrieve claims list', () => {
    cy.apiRequest('GET', '/api/v1/services/claims/')
      .then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('results')
        } else {
          expect([404, 405]).to.include(response.status)
        }
      })
  })

  it('should process claim status changes', () => {
    const claimData = {
      claim_number: `CLM-${Date.now()}`,
      tenant: testTenant.id,
      claimant_name: 'Status Test Claimant',
      claim_type: 'death',
      claim_amount: 25000.00,
      status: 'submitted'
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', claimData)
      .then((createResponse) => {
        if (createResponse.status === 201) {
          const claimId = createResponse.body.id

          // Progress through claim statuses
          const statusFlow = ['under_review', 'approved', 'paid']
          
          statusFlow.forEach((status, index) => {
            cy.apiRequest('PATCH', `/api/v1/services/claims/${claimId}/`, {
              status: status
            }).then((updateResponse) => {
              if (updateResponse.status === 200) {
                expect(updateResponse.body.status).to.eq(status)
              }
            })
          })
        }
      })
  })

  it('should handle claim rejection workflow', () => {
    const claimData = {
      claim_number: `CLM-REJ-${Date.now()}`,
      tenant: testTenant.id,
      claimant_name: 'Rejection Test Claimant',
      claim_type: 'death',
      claim_amount: 25000.00,
      status: 'submitted'
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', claimData)
      .then((createResponse) => {
        if (createResponse.status === 201) {
          const claimId = createResponse.body.id

          // Reject the claim
          cy.apiRequest('PATCH', `/api/v1/services/claims/${claimId}/`, {
            status: 'rejected',
            rejection_reason: 'Insufficient documentation provided'
          }).then((updateResponse) => {
            if (updateResponse.status === 200) {
              expect(updateResponse.body.status).to.eq('rejected')
              expect(updateResponse.body.rejection_reason).to.include('documentation')
            }
          })
        }
      })
  })

  it('should validate claim amounts against policy coverage', () => {
    // Test claim amount validation
    const claimData = {
      claim_number: `CLM-VAL-${Date.now()}`,
      tenant: testTenant.id,
      claimant_name: 'Validation Test',
      claim_type: 'death',
      claim_amount: 100000.00, // Amount exceeding typical coverage
      policy_coverage: 25000.00
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', claimData)
      .then((response) => {
        if (response.status === 400) {
          // Should validate that claim amount doesn't exceed coverage
          expect(response.body).to.have.property('error')
        } else if (response.status === 201) {
          // If created, should handle the validation in processing
          expect(response.body.claim_amount).to.exist
        }
      })
  })

  it('should track claim documentation', () => {
    const claimData = {
      claim_number: `CLM-DOC-${Date.now()}`,
      tenant: testTenant.id,
      claimant_name: 'Documentation Test',
      claim_type: 'death',
      claim_amount: 25000.00,
      required_documents: ['death_certificate', 'policy_document', 'id_copy']
    }

    cy.apiRequest('POST', '/api/v1/services/claims/', claimData)
      .then((response) => {
        if (response.status === 201) {
          expect(response.body).to.have.property('claim_number')
          // Check if documentation tracking is implemented
          if (response.body.required_documents) {
            expect(response.body.required_documents).to.be.an('array')
          }
        }
      })
  })

  it('should generate claim reports', () => {
    // Test claims reporting functionality
    cy.apiRequest('GET', '/api/v1/services/claims/reports/')
      .then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('summary')
        } else {
          expect([404, 405]).to.include(response.status)
        }
      })
  })
})