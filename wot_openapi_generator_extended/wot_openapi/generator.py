from flask import Flask, jsonify, request, make_response 
import string
import json
import string
import logging
import sys
import requests
from markupsafe import escape


app = Flask(__name__) # create an app instance
app.config['JSON_SORT_KEYS'] = False
logging.basicConfig(level=logging.DEBUG)   


### functions

def infoObject(td, userInput):

  info = userInput.get("info")
  infoObject = {}
  infoObject = info
  td['info'] = infoObject 



### API routes 

# just for testing 
@app.route('/', methods=['GET'])
def get_root():
  return "UP!"


# Create the SOAS description 
@app.route('/generator', methods=['POST'])
def create_oas():

  # Validate the request body contains JSON
  if request.is_json:

    # Parse the JSON into a Python dictionary  
    req = request.get_json()

    td = {}
    schemas = {} 

    td['openapi'] = "3.0.3"   
 
    infoObject(td, req) # create infoObject for the OpenAPI description 

    # Get Servers, ExternalDocs data from user input 
    externalDocs = req.get("externalDocs")
    servers = req.get("servers")

    if servers: 
      td['servers'] = servers  # create servers array for the OpenAPI description 

    # service security configuration settings (security schemes)
    securitySchemes = req.get("security_Schemes") 

    # service security configuration settings (security requirements)
    securityReqList = req.get("security_Req_List") 

    if externalDocs: 
      td['externalDocs'] = externalDocs

    if securityReqList:
      td['security'] = securityReqList # append Security Requirement Object to the document 
    else: 
      td['security'] = []  

    # Get device general type (sensor or actuator)
    type_of_thing = req.get("type_of_thing")

    if "sensor" not in type_of_thing:     
      thing_type = 'actuator'
      supported_actions = req.get("supported_actions") 
    else:
      thing_type = 'sensor'  

    # Get specific device category (door, car, window, air condition, etc)
    device_category = req.get("device_category")

    # if a specific device category has been defined 
    if device_category:       

      ########## door actuator --> ##########

      if "door" in device_category:
        
        default_webthing_schema = {

          "required": [
            "id",
            "name"
          ],
          "type": "object",
          "x-refersTo": "http://www.w3.org/ns/sosa/Actuator",
          "properties": {
            "id": {
              "type": "string",
              "default": "SmartDoor",
              "x-kindOf": "http://schema.org/identifier"
            },
            "name": {
              "type": "string",
              "example": "IoTSmartDoor",
              "x-kindOf": "http://schema.org/name"
            },
            "description": {
              "type": "string",
              "example": "A Smart Door is an electronic door which can be sent commands to be locked or unlocked remotely. It can also report on its current state (OPEN, CLOSED or LOCKED).",
              "x-refersTo": "http://schema.org/description"
            },
            "createdAt": {
              "type": "string",
              "format": "date-time"  
            },
            "updatedAt": {
              "type": "string",
              "format": "date-time"
            },
            "tags": {
              "type": "array",
              "items": {
                "type": "string",
                "example": "smart door"
              }
            }
          },
          "xml": {
            "name": "Webthing"
          }

        }

        webthing_schema = req.get("webthing_schema") # read Web Thing schema from user 

        if webthing_schema:
          # append Webthing Schema object to schemas 
          schemas['Webthing'] = webthing_schema
        else: 
          schemas['Webthing'] = default_webthing_schema

        # Get user's choice for subscription support (yes or no)
        sub_support = req.get("sub_support") 

        tags = [
          {
            "name": "Web Thing",
            "x-onResource": "'#/components/schemas/Webthing'",
            "description": "Operations on a Web Thing",
            "externalDocs": {
              "description": "Find out more",
              "url": "https://www.w3.org/Submission/wot-model/#web-thing-resource"
            }
          },
          {
            "name": "Properties",
            "description": "Operations on Thing Properties",
            "externalDocs": {
              "description": "Find out more about Thing properties",
              "url": "https://www.w3.org/Submission/wot-model/#properties-resource"
            }
          },
          {
            "name": "Actions",
            "description": "Operations on Thing Actions",
            "externalDocs": {
              "description": "Find out more about Thing Actions",
              "url": "https://www.w3.org/Submission/wot-model/#actions-resource"
            }
          },
          {
            "name": "Subscriptions",
            "x-onResource": "'#/components/schemas/SubscriptionObject'",
            "description": "Operations on subscriptions",
            "externalDocs": {
              "description": "Find out more about subscriptions",
              "url": "https://www.w3.org/Submission/wot-model/#things-resource"
            }
          }
        ]

        paths = {
          "/": {
            "get": {
              "tags": [
                "Web Thing"
              ],
              "summary": "Retrieve Web Thing",
              "description": "In response to an HTTP GET request on the root URL of a Thing, an Extended Web Thing must return an object that holds its representation.",
              "operationId": "retrieveWebThing",
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/Webthing"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          },
          "/properties": {
            "get": {
              "tags": [
                "Properties"   
              ],
              "summary": "Retrieve a list of properties",
              "description": "In response to an HTTP GET request on the destination URL of a properties link, an Extended Web Thing must return an array of Property that the initial resource contains.",
              "operationId": "retrieveWebThingProperties",
              "responses": {
                "200": {  
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/PropertiesResponse"
                        }
                      }
                    }
                  }
                },
                "400": {
                  "description": "Invalid ID supplied"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          }  

        }  

        # state property endpoint definition 
        retrieve_state_property_endpoint = {

          "get": {
            "tags": [
              "Properties"
            ],
            "summary": "Retrieve the value of a property (state)",
            "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
            "operationId": "retrieveStateProperty",
            "parameters": [
              {
                "$ref": "#/components/parameters/pageParam"
              },
              {
                "name": "perPage",
                "description": "Pagination second (per page) parameter",
                "in": "query",
                "required": bool(False),
                "schema": {
                  "type": "integer"
                }
              }
            ],
            "responses": {
              "200": {
                "description": "successful operation",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "array",
                      "items": {
                        "$ref": "#/components/schemas/State"
                      }
                    }
                  }
                }
              },
              "404": {
                "description": "Not found"
              }
            }
          }

        }    

        paths['/properties/state'] = retrieve_state_property_endpoint 

        # define PropertiesResponse schema "anyOf" array 
        properties_jsonobj = {
          "anyOf": [           
            { 
              "$ref": "#/components/schemas/StateProperty"
            } 
          ]
        }

        # Get the extra properties (if any) supported by the device
        extra_supported_properties = req.get("extra_supported_properties")
              
        # properties endpoints and schemas definition 
        if extra_supported_properties: 
          for i in range(len(extra_supported_properties)):
            extra_device_property = extra_supported_properties[i]
            extra_device_property_first_capital = string.capwords(extra_device_property) 

            #response_extra_property = {
            #  "$ref": "#/components/schemas/"+extra_device_property_first_capital+"Property"
            #}

            properties_jsonobj["anyOf"].append({ "$ref": "#/components/schemas/"+extra_device_property_first_capital+"Property" })
        
        properties_response_xml_name = {
          "name": "PropertiesResponse"
        }

        properties_jsonobj['xml'] = properties_response_xml_name

        # add PropertiesResponse schema to schemas 
        schemas['PropertiesResponse'] = properties_jsonobj


        # default state properties schemas definition 
        default_state_property_measurement_schema = {

          "type": "object",
          "x-kindOf": "http://www.w3.org/ns/sosa/Observation",
          "properties": {
            "state": {
              "type": "string",
              "x-kindOf": "http://www.w3.org/ns/sosa/hasSimpleResult",
              "enum": [
                "OPEN",
                "CLOSED",
                "LOCKED"
              ]
            },
            "timestamp": {
              "type": "string",
              "format": "date-time",
              "x-kindOf": "http://www.w3.org/ns/sosa/resultTime"
            }
          },
          "xml": {
            "name": "State"
          }

        }

        default_state_property_schema = {

          "required": [
            "id",
            "values"
          ],
          "x-kindOf": "http://www.w3.org/ns/ssn/systems/SystemCapability",
          "properties": {
            "id": {
              "type": "string",
              "default": "state",
              "x-kindOf": "http://schema.org/identifier"
            },
            "name": {
              "type": "string",
              "example": "Smart door's current state",
              "x-kindOf": "http://schema.org/name"
            },
            "values": {
              "$ref": "#/components/schemas/State"
            }
          },
          "xml": {
            "name": "StateProperty"
          }

        }    

        ### State property measurement schema ###

        # read state property measurement schema (if any) from user input to replace the default one
        state_property_measurement_schema = req.get("State")
        if state_property_measurement_schema: 
          # append State property measurement Schema object to schemas
          schemas['State'] = state_property_measurement_schema 
        else: 
          # append State property measurement Schema object to schemas
          schemas['State'] = default_state_property_measurement_schema         
        
        ### State property schema ###

        # read state property schema (if any) from user input to replace the default one
        state_property_schema = req.get("StateProperty")
        if state_property_schema: 
          # append State property Schema object to schemas
          schemas['StateProperty'] = state_property_schema 
        else: 
          # append State property Schema object to schemas
          schemas['StateProperty'] = default_state_property_schema 

        # extra properties endpoints definition 
        if extra_supported_properties: 
          for i in range(len(extra_supported_properties)):
            extra_device_property = extra_supported_properties[i]
            extra_device_property_first_capital = string.capwords(extra_device_property) 

            retrieve_extra_property_endpoint = {   

              "get": {
                "tags": [
                  "Properties"
                ],
                "summary": "Retrieve the value of a property ("+extra_device_property+")",
                "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
                "operationId": "retrieve"+extra_device_property_first_capital+"Property",
                "parameters": [
                  {
                    "$ref": "#/components/parameters/pageParam"
                  },
                  {
                    "name": "perPage",
                    "description": "Pagination second (per page) parameter",
                    "in": "query",
                    "required": bool(False),
                    "schema": {
                      "type": "integer"
                    }
                  }
                ],
                "responses": {
                  "200": {
                    "description": "successful operation",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "array",
                          "items": {
                            "$ref": "#/components/schemas/"+extra_device_property_first_capital+""
                          }
                        }
                      }
                    }
                  },
                  "404": {
                    "description": "Not found"
                  }
                }
              }

            }    

            paths['/properties/'+extra_device_property] = retrieve_extra_property_endpoint
            
            # read extra property measurement schema from user input 
            extra_property_measurement_schema = req.get(""+extra_device_property_first_capital+"MeasurementSchema")
            if extra_property_measurement_schema: 
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+''] = extra_property_measurement_schema
            else: 
              # default extra property measurement schema definition 
              default_extra_property_measurement_schema = {

                "type": "object",
                "x-kindOf": "http://www.w3.org/ns/sosa/Observation",
                "properties": {
                  ""+extra_device_property+"": {
                    "type": "string",
                    "x-kindOf": "http://www.w3.org/ns/sosa/hasSimpleResult"
                  },
                  "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "x-kindOf": "http://www.w3.org/ns/sosa/resultTime"
                  }
                },
                "xml": {
                  "name": ""+extra_device_property_first_capital+""
                }

              }    
          
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+''] = default_extra_property_measurement_schema  

            # read extra property schema from user input 
            extra_property_schema = req.get(""+extra_device_property_first_capital+"Schema")
            if extra_property_schema: 
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+'Property'] = extra_property_schema 
            else: 

              # default extra property schema definition 
              default_extra_property_schema = {   

                "required": [
                  "id",
                  "values"
                ],
                "x-kindOf": "http://www.w3.org/ns/ssn/systems/SystemCapability",
                "properties": {
                  "id": {
                    "type": "string",
                    "default": "state",
                    "x-kindOf": "http://schema.org/identifier"
                  },
                  "name": {
                    "type": "string",  
                    "example": "Smart door's current "+extra_device_property+"",    
                    "x-kindOf": "http://schema.org/name"
                  },
                  "values": {
                    "$ref": "#/components/schemas/"+extra_device_property_first_capital+""
                  }
                },
                "xml": {
                  "name": ""+extra_device_property_first_capital+"Property"
                }

              } 

              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+'Property'] = default_extra_property_schema 
            
            
        # if the device is a sensor 
        if thing_type != 'actuator': 
          for i in range(len(tags)): # remove Actions tag 
            if (i==2):
              tags.pop(i)
        # if the device is an actuator 
        else:

          retrieve_send_lock_execution_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve recent executions of the lock action",
              "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
              "operationId": "retrieveRecentExecutionsOfLockAction",
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionExecution"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Actions"
              ],
              "summary": "Execute a lock action",
              "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
              "operationId": "executeLockAction",
              "responses": {
                "204": {
                  "description": "NO RESPONSE"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/lock'] = retrieve_send_lock_execution_endpoint

          retrieve_lock_action_status_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve the status of a lock action",
              "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
              "parameters": [
                {
                  "name": "executionId",
                  "in": "path",
                  "description": "action execution of Webthing to return",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "format": "int64",
                      "default": 1
                    }
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/ActionExecution"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/lock/{executionId}'] = retrieve_lock_action_status_endpoint

          retrieve_send_unlock_execution_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve recent executions of the unlock action",
              "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
              "operationId": "retrieveRecentExecutionsOfUnlockAction",
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionExecution"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Actions"
              ],
              "summary": "Execute an unlock action",
              "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
              "operationId": "executeUnlockAction",
              "responses": {
                "204": {
                  "description": "NO RESPONSE"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/unlock'] = retrieve_send_unlock_execution_endpoint

          retrieve_unlock_action_status_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve the status of an unlock action",
              "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
              "parameters": [
                {
                  "name": "executionId",
                  "in": "path",
                  "description": "action execution of Webthing to return",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "format": "int64",
                      "default": 1
                    }
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/ActionExecution"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/unlock/{executionId}'] = retrieve_unlock_action_status_endpoint

          actions_endpoint = {

              "get": {
                "tags": [
                  "Actions"
                ],
                "summary": "Retrieve a list of actions",
                "operationId": "retrieveWebThingActions",
                "responses": {
                  "200": {
                    "description": "OK",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "array",
                          "items": {
                            "$ref": "#/components/schemas/ActionsResponse"
                          }
                        }
                      }
                    }
                  },
                  "404": {
                    "description": "Not found"
                  }
                }
              }

          }

          paths['/actions/'] = actions_endpoint

          # if extra supported actions have been defined in the input
          extra_supported_actions = req.get("extra_supported_actions")
          if extra_supported_actions: 

            for i in range(len(extra_supported_actions)):
              device_action = extra_supported_actions[i]
              device_action_first_capital = string.capwords(device_action) 
              extra_retrieve_send_execution_endpoint = {

                "get": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Retrieve recent executions of the "+device_action+" action",
                  "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
                  "operationId": "retrieveRecentExecutionsOf"+device_action_first_capital+"Action",
                  "responses": {
                    "200": {
                      "description": "successful operation",
                      "content": {
                        "application/json": {
                          "schema": {
                            "type": "array",
                            "items": {
                              "$ref": "#/components/schemas/ActionExecution"
                            }
                          }
                        }
                      }
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                },
                "post": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Execute a(n) "+device_action+" action",
                  "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
                  "operationId": "execute"+device_action+"Action",
                  "responses": {
                    "204": {
                      "description": "NO RESPONSE"
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                }

              }

              paths['/actions/'+device_action] = extra_retrieve_send_execution_endpoint

              extra_retrieve_action_status_endpoint = {

                "get": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Retrieve the status of a(n) "+device_action+" action",
                  "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
                  "parameters": [
                    {
                      "name": "executionId",
                      "in": "path",
                      "description": "action execution of Webthing to return",
                      "required": bool(True),
                      "style": "simple",
                      "explode": bool(True),
                      "schema": {
                        "type": "array",
                        "items": {
                          "type": "integer",
                          "format": "int64",
                          "default": 1
                        }
                      }
                    }     
                  ],
                  "responses": {
                    "200": {
                      "description": "OK",
                      "content": {
                        "application/json": {
                          "schema": {
                            "$ref": "#/components/schemas/ActionExecution"
                          }
                        }
                      }
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                }

              }

              paths['/actions/'+device_action+'/{executionId}'] = extra_retrieve_action_status_endpoint

            # define general /actions schema 
            default_action_schema = {

              "required": [
                "id",
                "name"
              ],
              "type": "object",
              "properties": {
                "id": {
                  "type": "string",
                  "example": "lock"
                },
                "name": {
                  "type": "string",
                  "example": "Lock the Smart Door"
                }
              },
              "xml": {
                "name": "Action"
              }
              
            }  

            default_action_execution_schema = {  

              "required": [
                "id",
                "status",
                "timestamp"
              ],
              "x-kindOf": "http://www.w3.org/ns/sosa/Actuation",
              "type": "object",
              "properties": {
                "id": {
                  "type": "string",
                  "example": "223"
                },
                "status": {
                  "type": "string",
                  "example": "completed"
                },
                "timestamp": {
                  "type": "string",
                  "format": "date-time"
                }
              },
              "xml": {
                "name": "ActionExecution"
              }

            }

            # define (default) ActionsResponse schema
            actions_jsonobj = {
              "anyOf": [           
                { 
                  "$ref": "#/components/schemas/Action"
                }
              ],
              "xml": {
                "name": "ActionsResponse"
              }
            }

            # append (default) ActionsResponse schema to schemas
            schemas['ActionsResponse'] = actions_jsonobj

            ### action schema ###

            # read action schema (if any) from user input to replace the default one
            action_schema = req.get("action_schema")
            if action_schema: 
              # append action Schema object to schemas
              schemas['Action'] = action_schema
            else: 
              # append action Schema object to schemas
              schemas['Action'] = default_action_schema

            ### action execution schema ###

            # read action execution schema (if any) from user input to replace the default one
            action_execution_schema = req.get("action_execution_schema")
            if action_execution_schema: 
              # append action execution Schema object to schemas
              schemas['ActionExecution'] = action_execution_schema
            else: 
              # append action execution Schema object to schemas
              schemas['ActionExecution'] = default_action_execution_schema     


        if sub_support=='yes':

          subscriptions_endpoints = {
            
            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve a list of subscriptions",
              "description": "In response to an HTTP GET request on the destination URL of a subscriptions link, an Extended Web Thing must return the array of subscriptions to the underlying resource.",
              "operationId": "retrieveListOfSubscriptions",
              "parameters": [
                {
                  "$ref": "#/components/parameters/pageParam"
                },
                {
                  "name": "perPage",
                  "description": "Pagination second (per page) parameter",
                  "in": "query",
                  "required": bool(False),
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/SubscriptionObject"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Create a subscription",
              "description": "An Extended Web Thing should support subscriptions for the specific resource (DHT22).",
              "operationId": "createSubscription",
              "x-operationType": "https://schema.org/CreateAction",
              "requestBody": {
                "description": "Create a new subscription",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/SubscriptionRequestBody"
                    }
                  }
                },
                "required": bool(True)
              },
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          
          } 

          #append /subscriptions endpoints and operations
          paths['/subscriptions/'] = subscriptions_endpoints

          # define /{subscriptionID} endpoints 
          subscriptionID_endpoints = { 

            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve information about a specific subscription",
              "description": "In response to an HTTP GET request on a Subscription URL, an Extended Web Thing must return a JSON representation of the subscription. The JSON representation should be the same as the one returned for that subscription in 'Retrieve a list of subscriptions'.",
              "operationId": "retreiveInfoAboutSubscription",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "x-mapsTo": "#/components/schemas/SubscriptionObject.id",
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/SubscriptionObject"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "delete": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Delete a subscription",
              "description": "In response to an HTTP DELETE request on the destination URL of a subscriptions an Extended Web Thing must either reject  the request with an appropriate status code or remove (unsubscribe) the subscription and return a 200 OK status code.",
              "operationId": "deleteSubscription",
              "x-operationType": "https://schema.org/DeleteAction",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          #append /subscriptions/{subscriptionID} endpoints and operations
          paths['/subscriptions/{subscriptionID}'] = subscriptionID_endpoints   

          #define subscription schemas 
          subscriptionRequestBody = {

            "required": [
              "description",
              "type",
              "callbackUrl",
              "resource"
            ],
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "example": "My subscription for SmartDoor's current state"
              },
              "description": {
                "type": "string",
                "example": "A subscription to get info about SmartDoor's current state"
              },
              "type": {
                "type": "string",
                "example": "webhook (callback)"
              },
              "callbackUrl": {
                "type": "string",
                "example": "http://172.16.1.5:5000/accumulate"
              },
              "resource": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string",
                    "example": "property"
                  },
                  "name": {
                    "type": "string",
                    "example": "state"
                  }
                }
              },
              "expires": {
                "type": "string",
                "format": "date-time"
              },
              "throttling": {
                "type": "integer",
                "format": "int32",
                "example": 5
              }
            },
            "xml": {
              "name": "SubscriptionRequestBody"
            }
          }

          subscriptionObject = {

            "allOf": [
              {
                "required": [
                  "id",
                  "type",
                  "resource",
                  "description",
                  "callbackUrl"
                ],
                "type": "object",
                "properties": {
                  "id": {
                    "type": "string",
                    "example": "5fc978fc96cc26a4e202c3d6"
                  }
                }
              },
              {
                "$ref": "#/components/schemas/SubscriptionRequestBody"
              }
            ],
            "xml": {
              "name": "SubscriptionObject"
            }
          } 

          # append subscription Schema objects to schemas 
          schemas['SubscriptionRequestBody'] = subscriptionRequestBody   
          schemas['SubscriptionObject'] = subscriptionObject

        else:
          for i in range(len(tags)): # remove Subscriptions tag 
            if (i==3):
              tags.pop(i)

        parameters = {
          
          "pageParam": {
            "name": "page",
            "description": "Pagination first (page) parameter",
            "in": "query",
            "required": bool(False),
            "schema": {
              "type": "integer"
            }
          }

        }

        # append tags to the description 
        td['tags'] = tags 
        # append paths to the description 
        td['paths'] = paths 

        componentsObject = {} # initialize Components object
        componentsObject['schemas'] = schemas
        componentsObject['parameters'] = parameters 
        
        if securitySchemes:
          componentsObject['securitySchemes'] = security_Schemes  # append securitySchemes to Components object 
        else: 
          componentsObject['securitySchemes'] = {} # append securitySchemes to Components object 

        td['components'] = componentsObject # append Components object to the document 

      ########## <-- door actuator ##########

      ########## airCondition actuator --> ##########

      elif "airCondition" in device_category:
        
        default_webthing_schema = {

          "required": [
            "id",
            "name",
            "type"
          ],
          "type": "object",
          "x-refersTo": "http://www.w3.org/ns/sosa/Actuator",
          "properties": {
            "id": {
              "type": "string",
              "default": "AirCondition",
              "x-kindOf": "http://schema.org/identifier"
            },
            "name": {
              "type": "string",
              "example": "IoTAirCondition_actuator",
              "x-kindOf": "http://schema.org/name"
            },
            "description": {
              "type": "string",
              "example": "An air condition is an electronic device which can be turned on or off remotely. It can also report on its current state (ON or OFF).",
              "x-refersTo": "http://schema.org/description"
            },
            "createdAt": {
              "type": "string",
              "format": "date-time"
            },
            "updatedAt": {
              "type": "string",
              "format": "date-time"
            },
            "tags": {
              "type": "array",
              "items": {
                "type": "string",
                "example": "air condition"
              }
            }
          },
          "xml": {
            "name": "Webthing"
          }

        }

        webthing_schema = req.get("webthing_schema") # read Web Thing schema from user 

        if webthing_schema:
          # append Webthing Schema object to schemas 
          schemas['Webthing'] = webthing_schema
        else: 
          schemas['Webthing'] = default_webthing_schema

        # Get user's choice for subscription support (yes or no)
        sub_support = req.get("sub_support") 

        tags = [
          {
            "name": "Web Thing",
            "x-onResource": "'#/components/schemas/Webthing'",
            "description": "Operations on a Web Thing",
            "externalDocs": {
              "description": "Find out more",
              "url": "https://www.w3.org/Submission/wot-model/#web-thing-resource"
            }
          },
          {
            "name": "Properties",
            "description": "Operations on Thing Properties",
            "externalDocs": {
              "description": "Find out more about Thing properties",
              "url": "https://www.w3.org/Submission/wot-model/#properties-resource"
            }
          },
          {
            "name": "Actions",
            "description": "Operations on Thing Actions",
            "externalDocs": {
              "description": "Find out more about Thing Actions",
              "url": "https://www.w3.org/Submission/wot-model/#actions-resource"
            }
          },
          {
            "name": "Subscriptions",
            "x-onResource": "'#/components/schemas/SubscriptionObject'",
            "description": "Operations on subscriptions",
            "externalDocs": {
              "description": "Find out more about subscriptions",
              "url": "https://www.w3.org/Submission/wot-model/#things-resource"
            }
          }
        ]

        paths = {
          "/": {
            "get": {
              "tags": [
                "Web Thing"
              ],
              "summary": "Retrieve Web Thing",
              "description": "In response to an HTTP GET request on the root URL of a Thing, an Extended Web Thing must return an object that holds its representation.",
              "operationId": "retrieveWebThing",
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/Webthing"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          },
          "/properties": {
            "get": {
              "tags": [
                "Properties"   
              ],
              "summary": "Retrieve a list of properties",
              "description": "In response to an HTTP GET request on the destination URL of a properties link, an Extended Web Thing must return an array of Property that the initial resource contains.",
              "operationId": "retrieveWebThingProperties",
              "responses": {
                "200": {  
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/PropertiesResponse"
                        }
                      }
                    }
                  }
                },
                "400": {
                  "description": "Invalid ID supplied"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          }  

        }  

        # state property endpoint definition 
        retrieve_state_property_endpoint = {

          "get": {
            "tags": [
              "Properties"
            ],
            "summary": "Retrieve the value of a property (AC ON or OFF)",
            "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
            "operationId": "retrieveProperty",
            "parameters": [
              {
                "$ref": "#/components/parameters/pageParam"
              },
              {
                "name": "perPage",
                "description": "Pagination second (per page) parameter",
                "in": "query",
                "required": bool(False),
                "schema": {
                  "type": "integer"
                }
              }
            ],
            "responses": {
              "200": {
                "description": "successful operation",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "array",
                      "items": {
                        "$ref": "#/components/schemas/State"
                      }
                    }
                  }
                }
              },
              "404": {
                "description": "Not found"
              }
            }
          }

        }    

        paths['/properties/state'] = retrieve_state_property_endpoint 

        # define PropertiesResponse schema "anyOf" array 
        properties_jsonobj = {
          "anyOf": [           
            { 
              "$ref": "#/components/schemas/StateProperty"
            } 
          ]
        }

        # Get the extra properties (if any) supported by the device
        extra_supported_properties = req.get("extra_supported_properties")
              
        # properties endpoints and schemas definition 
        if extra_supported_properties: 
          for i in range(len(extra_supported_properties)):
            extra_device_property = extra_supported_properties[i]
            extra_device_property_first_capital = string.capwords(extra_device_property) 

            #response_extra_property = {
            #  "$ref": "#/components/schemas/"+extra_device_property_first_capital+"Property"
            #}

            properties_jsonobj["anyOf"].append({ "$ref": "#/components/schemas/"+extra_device_property_first_capital+"Property" })
        
        properties_response_xml_name = {
          "name": "PropertiesResponse"
        }

        properties_jsonobj['xml'] = properties_response_xml_name

        # add PropertiesResponse schema to schemas 
        schemas['PropertiesResponse'] = properties_jsonobj


        # default state properties schemas definition 
        default_state_property_measurement_schema = {

          "type": "object",
          "x-kindOf": "http://www.w3.org/ns/sosa/Observation",
          "properties": {
            "state": {
              "type": "string",
              "x-kindOf": "http://www.w3.org/ns/sosa/hasSimpleResult",
              "enum": [
                "ON",
                "OFF"
              ]
            },
            "timestamp": {
              "type": "string",
              "format": "date-time",
              "x-kindOf": "http://www.w3.org/ns/sosa/resultTime"
            }
          },
          "xml": {
            "name": "State"
          }

        }

        default_state_property_schema = {

          "required": [
            "id",
            "values"
          ],
          "x-kindOf": "http://www.w3.org/ns/ssn/systems/SystemCapability",
          "properties": {
            "id": {
              "type": "string",   
              "default": "state",
              "x-kindOf": "http://schema.org/identifier"
            },
            "name": {
              "type": "string",
              "example": "Air condition's current state",
              "x-kindOf": "http://schema.org/name"
            },
            "values": {
              "$ref": "#/components/schemas/State"
            }
          },
          "xml": {
            "name": "StateProperty"
          }

        }    

        ### State property measurement schema ###

        # read state property measurement schema (if any) from user input to replace the default one
        state_property_measurement_schema = req.get("State")
        if state_property_measurement_schema: 
          # append State property measurement Schema object to schemas
          schemas['State'] = state_property_measurement_schema 
        else: 
          # append State property measurement Schema object to schemas
          schemas['State'] = default_state_property_measurement_schema         
        
        ### State property schema ###

        # read state property schema (if any) from user input to replace the default one
        state_property_schema = req.get("StateProperty")
        if state_property_schema: 
          # append State property Schema object to schemas
          schemas['StateProperty'] = state_property_schema 
        else: 
          # append State property Schema object to schemas
          schemas['StateProperty'] = default_state_property_schema 

        # extra properties endpoints definition 
        if extra_supported_properties: 
          for i in range(len(extra_supported_properties)):
            extra_device_property = extra_supported_properties[i]
            extra_device_property_first_capital = string.capwords(extra_device_property) 

            retrieve_extra_property_endpoint = {   

              "get": {
                "tags": [
                  "Properties"
                ],
                "summary": "Retrieve the value of a property ("+extra_device_property+")",
                "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
                "operationId": "retrieve"+extra_device_property_first_capital+"Property",
                "parameters": [
                  {
                    "$ref": "#/components/parameters/pageParam"
                  },
                  {
                    "name": "perPage",
                    "description": "Pagination second (per page) parameter",
                    "in": "query",
                    "required": bool(False),
                    "schema": {
                      "type": "integer"
                    }
                  }
                ],
                "responses": {
                  "200": {
                    "description": "successful operation",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "array",
                          "items": {
                            "$ref": "#/components/schemas/"+extra_device_property_first_capital+""
                          }
                        }
                      }
                    }
                  },
                  "404": {
                    "description": "Not found"
                  }
                }
              }

            }    

            paths['/properties/'+extra_device_property] = retrieve_extra_property_endpoint
            
            # read extra property measurement schema from user input 
            extra_property_measurement_schema = req.get(""+extra_device_property_first_capital+"MeasurementSchema")
            if extra_property_measurement_schema: 
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+''] = extra_property_measurement_schema
            else: 
              # default extra property measurement schema definition 
              default_extra_property_measurement_schema = {

                "type": "object",
                "x-kindOf": "http://www.w3.org/ns/sosa/Observation",
                "properties": {
                  ""+extra_device_property+"": {
                    "type": "string",
                    "x-kindOf": "http://www.w3.org/ns/sosa/hasSimpleResult"
                  },
                  "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "x-kindOf": "http://www.w3.org/ns/sosa/resultTime"
                  }
                },
                "xml": {
                  "name": ""+extra_device_property_first_capital+""
                }

              }    
          
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+''] = default_extra_property_measurement_schema  

            # read extra property schema from user input 
            extra_property_schema = req.get(""+extra_device_property_first_capital+"Schema")
            if extra_property_schema: 
              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+'Property'] = extra_property_schema 
            else: 

              # default extra property schema definition 
              default_extra_property_schema = {   

                "required": [
                  "id",
                  "values"
                ],
                "x-kindOf": "http://www.w3.org/ns/ssn/systems/SystemCapability",
                "properties": {
                  "id": {
                    "type": "string",
                    "default": "state",
                    "x-kindOf": "http://schema.org/identifier"
                  },
                  "name": {
                    "type": "string",  
                    "example": "Smart door's current "+extra_device_property+"",    
                    "x-kindOf": "http://schema.org/name"
                  },
                  "values": {
                    "$ref": "#/components/schemas/"+extra_device_property_first_capital+""
                  }
                },
                "xml": {
                  "name": ""+extra_device_property_first_capital+"Property"
                }

              } 

              # append extra property measurement Schema object to schemas
              schemas[''+extra_device_property_first_capital+'Property'] = default_extra_property_schema 
            
            
        # if the device is a sensor 
        if thing_type != 'actuator': 
          for i in range(len(tags)): # remove Actions tag 
            if (i==2):
              tags.pop(i)
        # if the device is an actuator 
        else:

          retrieve_send_switchon_execution_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve recent executions of the switch on action",
              "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
              "operationId": "retrieveRecentExecutionsOfswitchOnAction",
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionExecution"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Actions"
              ],
              "summary": "Execute a switch on action",
              "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
              "operationId": "executeSwitchOnAction",
              "requestBody": {
                "description": "Request body to switch on the AC",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/SwitchOnRequestBody"
                    }
                  }
                },
                "required": bool(False)
              },
              "responses": {
                "204": {
                  "description": "NO RESPONSE"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/switchOn'] = retrieve_send_switchon_execution_endpoint

          retrieve_switchon_action_status_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve the status of a switch on action",
              "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
              "parameters": [
                {
                  "name": "executionId",
                  "in": "path",
                  "description": "action execution of Webthing to return",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "format": "int64",
                      "default": 1
                    }
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/ActionExecution"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/switchOn/{executionId}'] = retrieve_switchon_action_status_endpoint

          retrieve_send_switchoff_execution_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve recent executions of the switch off action",
              "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
              "operationId": "retrieveRecentExecutionsOfswitchOffAction",
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionExecution"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Actions"
              ],
              "summary": "Execute an switch off action",
              "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
              "operationId": "executeSwitchOffAction",
              "requestBody": {
                "description": "Request body to switch off the AC",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/SwitchOnRequestBody"
                    }
                  }
                },
                "required": bool(False)
              },
              "responses": {
                "204": {
                  "description": "NO RESPONSE"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/switchOff'] = retrieve_send_switchoff_execution_endpoint

          retrieve_switchoff_action_status_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve the status of a switch off action",
              "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
              "parameters": [
                {
                  "name": "executionId",
                  "in": "path",
                  "description": "action execution of Webthing to return",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "format": "int64",
                      "default": 1
                    }
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/ActionExecution"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/switchOff/{executionId}'] = retrieve_switchoff_action_status_endpoint

          actions_endpoint = {

              "get": {
                "tags": [
                  "Actions"
                ],
                "summary": "Retrieve a list of actions",
                "operationId": "retrieveWebThingActions",
                "responses": {
                  "200": {
                    "description": "OK",
                    "content": {
                      "application/json": {
                        "schema": {
                          "type": "array",
                          "items": {
                            "$ref": "#/components/schemas/ActionsResponse"
                          }
                        }
                      }
                    }
                  },
                  "404": {
                    "description": "Not found"
                  }
                }
              }

          }

          paths['/actions/'] = actions_endpoint

          # if extra supported actions have been defined in the input
          extra_supported_actions = req.get("extra_supported_actions")
          if extra_supported_actions: 

            for i in range(len(extra_supported_actions)):
              device_action = extra_supported_actions[i]
              device_action_first_capital = string.capwords(device_action)
              extra_retrieve_send_execution_endpoint = {

                "get": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Retrieve recent executions of the "+device_action+" action",
                  "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
                  "operationId": "retrieveRecentExecutionsOf"+device_action_first_capital+"Action",
                  "responses": {
                    "200": {
                      "description": "successful operation",
                      "content": {
                        "application/json": {
                          "schema": {
                            "type": "array",
                            "items": {
                              "$ref": "#/components/schemas/ActionExecution"
                            }
                          }
                        }
                      }
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                },
                "post": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Execute a(n) "+device_action+" action",
                  "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
                  "operationId": "execute"+device_action_first_capital+"Action",
                  "responses": {
                    "204": {
                      "description": "NO RESPONSE"
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                }

              }

              paths['/actions/'+device_action] = extra_retrieve_send_execution_endpoint

              extra_retrieve_action_status_endpoint = {

                "get": {
                  "tags": [
                    "Actions"
                  ],
                  "summary": "Retrieve the status of a(n) "+device_action+" action",
                  "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
                  "parameters": [
                    {
                      "name": "executionId",
                      "in": "path",
                      "description": "action execution of Webthing to return",
                      "required": bool(True),
                      "style": "simple",
                      "explode": bool(True),
                      "schema": {
                        "type": "array",
                        "items": {
                          "type": "integer",
                          "format": "int64",
                          "default": 1
                        }
                      }
                    }     
                  ],
                  "responses": {
                    "200": {
                      "description": "OK",
                      "content": {
                        "application/json": {
                          "schema": {
                            "$ref": "#/components/schemas/ActionExecution"
                          }
                        }
                      }
                    },
                    "404": {
                      "description": "Not found"
                    }
                  }
                }

              }

              paths['/actions/'+device_action+'/{executionId}'] = extra_retrieve_action_status_endpoint

          # define general /actions schema 
          default_action_schema = {

            "required": [
              "id",
              "name"
            ],
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "example": "switch on"
              },
              "name": {
                "type": "string",
                "example": "Switch on the Air Condition"
              }
            },
            "xml": {
              "name": "Action"
            }
            
          }  

          default_action_execution_schema = {  

            "required": [
              "id",
              "status",   
              "timestamp"
            ],
            "x-kindOf": "http://www.w3.org/ns/sosa/Actuation",
            "type": "object",
            "properties": {
              "id": {
                "type": "string",
                "example": "223"
              },
              "status": {
                "type": "string",
                "example": "completed"
              },
              "timestamp": {
                "type": "string",
                "format": "date-time"
              }
            },
            "xml": {
              "name": "ActionExecution"
            }

          }

          # define (default) ActionsResponse schema
          actions_jsonobj = {
            "anyOf": [           
              { 
                "$ref": "#/components/schemas/Action"
              }
            ],
            "xml": {
              "name": "ActionsResponse"
            }
          }

          # append (default) ActionsResponse schema to schemas
          schemas['ActionsResponse'] = actions_jsonobj

          ### action schema ###

          # read action schema (if any) from user input to replace the default one
          action_schema = req.get("action_schema")
          if action_schema: 
            # append action Schema object to schemas
            schemas['Action'] = action_schema
          else: 
            # append action Schema object to schemas
            schemas['Action'] = default_action_schema

          ### action execution schema ###

          # read action execution schema (if any) from user input to replace the default one
          action_execution_schema = req.get("action_execution_schema")
          if action_execution_schema: 
            # append action execution Schema object to schemas
            schemas['ActionExecution'] = action_execution_schema
          else: 
            # append action execution Schema object to schemas
            schemas['ActionExecution'] = default_action_execution_schema  

          SwitchOnRequestBodySchema = {

            "required": [
              "type",
              "Thing",
              "name", 
              "status",
              "timestamp"
            ],  
            "type": "object",
            "properties": {
              "type": {
                "type": "string",
                "example": "execution"
              },
              "Thing": {
                "type": "string",
                "example": "AirCondition_actuator"
              },
              "name": {
                "type": "string",
                "example": "switchOn"
              },
              "status": {
                "type": "string",
                "example": "executing"
              },
              "timestamp": {
                "type": "string",
                "format": "date-time"
              },
              "value": {
                "type": "object",
                "properties": {
                  "delay": {
                    "type": "integer",
                    "format": "int32",
                    "example": 50
                  }
                }
              }
            },
            "xml": {
              "name": "SwitchOnRequestBody"
            }

          }   

          # append SwitchOnRequestBody Schema object to schemas 
          schemas['SwitchOnRequestBody'] = SwitchOnRequestBodySchema


        if sub_support=='yes':

          subscriptions_endpoints = {
            
            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve a list of subscriptions",
              "description": "In response to an HTTP GET request on the destination URL of a subscriptions link, an Extended Web Thing must return the array of subscriptions to the underlying resource.",
              "operationId": "retrieveListOfSubscriptions",
              "parameters": [
                {
                  "$ref": "#/components/parameters/pageParam"
                },
                {
                  "name": "perPage",
                  "description": "Pagination second (per page) parameter",
                  "in": "query",
                  "required": bool(False),
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/SubscriptionObject"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Create a subscription",
              "description": "An Extended Web Thing should support subscriptions for the specific resource (DHT22).",
              "operationId": "createSubscription",
              "x-operationType": "https://schema.org/CreateAction",
              "requestBody": {
                "description": "Create a new subscription",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/SubscriptionRequestBody"
                    }
                  }
                },
                "required": bool(True)
              },
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          
          } 

          #append /subscriptions endpoints and operations
          paths['/subscriptions/'] = subscriptions_endpoints

          # define /{subscriptionID} endpoints 
          subscriptionID_endpoints = { 

            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve information about a specific subscription",
              "description": "In response to an HTTP GET request on a Subscription URL, an Extended Web Thing must return a JSON representation of the subscription. The JSON representation should be the same as the one returned for that subscription in 'Retrieve a list of subscriptions'.",
              "operationId": "retreiveInfoAboutSubscription",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "x-mapsTo": "#/components/schemas/SubscriptionObject.id",
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/SubscriptionObject"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "delete": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Delete a subscription",
              "description": "In response to an HTTP DELETE request on the destination URL of a subscriptions an Extended Web Thing must either reject  the request with an appropriate status code or remove (unsubscribe) the subscription and return a 200 OK status code.",
              "operationId": "deleteSubscription",
              "x-operationType": "https://schema.org/DeleteAction",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          #append /subscriptions/{subscriptionID} endpoints and operations
          paths['/subscriptions/{subscriptionID}'] = subscriptionID_endpoints   

          #define subscription schemas 
          subscriptionRequestBody = {

            "required": [
              "description",
              "type",
              "callbackUrl",
              "resource"
            ],
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "example": "My subscription for SmartDoor's current state"
              },
              "description": {
                "type": "string",
                "example": "A subscription to get info about SmartDoor's current state"
              },
              "type": {
                "type": "string",
                "example": "webhook (callback)"
              },
              "callbackUrl": {
                "type": "string",
                "example": "http://172.16.1.5:5000/accumulate"
              },
              "resource": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string",
                    "example": "property"
                  },
                  "name": {
                    "type": "string",
                    "example": "state"
                  }
                }
              },
              "expires": {
                "type": "string",
                "format": "date-time"
              },
              "throttling": {
                "type": "integer",
                "format": "int32",
                "example": 5
              }
            },
            "xml": {
              "name": "SubscriptionRequestBody"
            }
          }

          subscriptionObject = {

            "allOf": [
              {
                "required": [
                  "id",
                  "type",
                  "resource",
                  "description",
                  "callbackUrl"
                ],
                "type": "object",
                "properties": {
                  "id": {
                    "type": "string",
                    "example": "5fc978fc96cc26a4e202c3d6"
                  }
                }
              },
              {
                "$ref": "#/components/schemas/SubscriptionRequestBody"
              }
            ],
            "xml": {
              "name": "SubscriptionObject"
            }
          } 

          # append subscription Schema objects to schemas 
          schemas['SubscriptionRequestBody'] = subscriptionRequestBody   
          schemas['SubscriptionObject'] = subscriptionObject

        else:
          for i in range(len(tags)): # remove Subscriptions tag 
            if (i==3):
              tags.pop(i)

        parameters = {
          
          "pageParam": {
            "name": "page",
            "description": "Pagination first (page) parameter",
            "in": "query",
            "required": bool(False),
            "schema": {
              "type": "integer"
            }
          }

        }

        # append tags to the description 
        td['tags'] = tags 
        # append paths to the description 
        td['paths'] = paths 

        componentsObject = {} # initialize Components object
        componentsObject['schemas'] = schemas
        componentsObject['parameters'] = parameters 

        if securitySchemes:
          componentsObject['securitySchemes'] = security_Schemes  # append securitySchemes to Components object 
        else: 
          componentsObject['securitySchemes'] = {} # append securitySchemes to Components object 
        
        td['components'] = componentsObject # append Components object to the document 

      ########## <-- airCondition actuator ##########

      else:
        td['device_category'] = {}

    # else just create the device instance using the general Thing template 
    else: 

      schemas = {}

      default_webthing_schema = {  

        "required": [
          "id",
          "name"
        ],
        "type": "object",
        "properties": {
          "id": {
            "type": "string",  
            "x-kindOf": "http://schema.org/identifier"
          },
          "name": {
            "type": "string",
            "x-kindOf": "http://schema.org/name"
          },
          "description": {
            "type": "string",
            "example": "A Smart Door is an electronic door which can be sent commands to be locked or unlocked remotely. It can also report on its current state (OPEN, CLOSED or LOCKED).",
            "x-refersTo": "http://schema.org/description"
          },
          "createdAt": {
            "type": "string",
            "format": "date-time"  
          },
          "updatedAt": {
            "type": "string",
            "format": "date-time"
          },
          "tags": {
            "type": "array",
            "items": {
              "type": "string",
              "example": "device"
            }
          }
        },
        "xml": {
          "name": "Webthing"
        }

      }

      webthing_schema = req.get("webthing_schema") # read Web Thing schema from user input 

      if webthing_schema:
        # append Webthing Schema object to schemas 
        schemas['Webthing'] = webthing_schema
      else: 
        schemas['Webthing'] = default_webthing_schema

      # Get the Properties supported by the device
      supported_properties = req.get("supported_properties")

      # Get user's choice for subscription support (yes or no)
      sub_support = req.get("sub_support") 

      tags = [
        {
          "name": "Web Thing",
          "x-onResource": "'#/components/schemas/Webthing'",
          "description": "Operations on a Web Thing",
          "externalDocs": {
            "description": "Find out more",
            "url": "https://www.w3.org/Submission/wot-model/#web-thing-resource"
          }
        },
        {
          "name": "Properties",
          "description": "Operations on Thing Properties",
          "externalDocs": {
            "description": "Find out more about Thing properties",
            "url": "https://www.w3.org/Submission/wot-model/#properties-resource"
          }
        },
        {
          "name": "Actions",
          "description": "Operations on Thing Actions",
          "externalDocs": {
            "description": "Find out more about Thing Actions",
            "url": "https://www.w3.org/Submission/wot-model/#actions-resource"
          }
        },
        {
          "name": "Subscriptions",
          "x-onResource": "'#/components/schemas/SubscriptionObject'",
          "description": "Operations on subscriptions",
          "externalDocs": {
            "description": "Find out more about subscriptions",
            "url": "https://www.w3.org/Submission/wot-model/#things-resource"
          }
        }
      ]

      paths = {
        "/": {
          "get": {
            "tags": [
              "Web Thing"
            ],
            "summary": "Retrieve Web Thing",
            "description": "In response to an HTTP GET request on the root URL of a Thing, an Extended Web Thing must return an object that holds its representation.",
            "operationId": "retrieveWebThing",
            "responses": {
              "200": {
                "description": "OK",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/Webthing"
                    }
                  }
                }
              },
              "404": {
                "description": "Not found"
              }
            }
          }
        },
        "/properties": {
          "get": {
            "tags": [
              "Properties"
            ],
            "summary": "Retrieve a list of properties",
            "description": "In response to an HTTP GET request on the destination URL of a properties link, an Extended Web Thing must return an array of Property that the initial resource contains.",
            "operationId": "retrieveWebThingProperties",
            "responses": {
              "200": {
                "description": "OK",
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "array",
                      "items": {
                        "$ref": "#/components/schemas/PropertiesResponse"
                      }
                    }
                  }
                }
              },
              "400": {
                "description": "Invalid ID supplied"
              },
              "404": {
                "description": "Not found"
              }
            }
          }
        }  

      }

      # define PropertiesResponse schema "anyOf" array 
      properties_jsonobj = {  
        "anyOf": []
      }

      # properties endpoints and schemas definition 
      if supported_properties: 
        for i in range(len(supported_properties)):
          device_property = supported_properties[i]  
          device_property_first_capital = string.capwords(device_property) 

          retrieve_property_endpoint = {

            "get": {
              "tags": [
                "Properties"
              ],
              "summary": "Retrieve the value of a property ("+device_property+")",
              "description": "In response to an HTTP GET request on a Property URL, an Extended Web Thing must return an array that lists recent values of that Property.",
              "operationId": "retrieve"+device_property_first_capital+"Property",
              "parameters": [
                {
                  "$ref": "#/components/parameters/pageParam"
                },
                {
                  "name": "perPage",
                  "description": "Pagination second (per page) parameter",
                  "in": "query",
                  "required": bool(False),
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/"+device_property_first_capital+""
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }      

          paths['/properties/'+device_property] = retrieve_property_endpoint
          
          properties_jsonobj["anyOf"].append({ "$ref": "#/components/schemas/"+device_property_first_capital+"Property" })
        
          properties_response_xml_name = {
            "name": "PropertiesResponse"
          }

          properties_jsonobj['xml'] = properties_response_xml_name

          # add PropertiesResponse schema to schemas 
          schemas['PropertiesResponse'] = properties_jsonobj

          # read extra property measurement schema from user input 
          device_property_measurement_schema = req.get(""+device_property_first_capital+"MeasurementSchema")
          if device_property_measurement_schema: 
            # append extra property measurement Schema object to schemas
            schemas[''+device_property_first_capital+''] = device_property_measurement_schema
          else: 
            # default extra property measurement schema definition 
            default_device_property_measurement_schema = {   

              "type": "object",
              "x-kindOf": "http://www.w3.org/ns/sosa/Observation",
              "properties": {
                ""+device_property+"": {
                  "type": "string",  
                  "x-kindOf": "http://www.w3.org/ns/sosa/hasSimpleResult"
                },
                "timestamp": {
                  "type": "string",
                  "format": "date-time",
                  "x-kindOf": "http://www.w3.org/ns/sosa/resultTime"
                }
              },
              "xml": {
                "name": ""+device_property_first_capital+""
              }

            }                
        
            # append extra property measurement Schema object to schemas
            schemas[''+device_property_first_capital+''] = default_device_property_measurement_schema  

          # read extra property schema from user input 
          device_property_schema = req.get(""+device_property_first_capital+"Schema")
          if device_property_schema: 
            # append extra property measurement Schema object to schemas
            schemas[''+device_property_first_capital+'Property'] = device_property_schema 
          else: 

            # default extra property schema definition 
            default_device_property_schema = {             

              "required": [
                "id",
                "values"
              ],
              "x-kindOf": "http://www.w3.org/ns/ssn/systems/SystemCapability",
              "properties": {
                "id": {
                  "type": "string",
                  "default": "state",
                  "x-kindOf": "http://schema.org/identifier"
                },
                "name": {
                  "type": "string",  
                  "example": "Smart door's current "+device_property+"",    
                  "x-kindOf": "http://schema.org/name"
                },
                "values": {
                  "$ref": "#/components/schemas/"+device_property_first_capital+""
                }
              },
              "xml": {
                "name": ""+device_property_first_capital+"Property"
              }

            }    

            # append extra property measurement Schema object to schemas
            schemas[''+device_property_first_capital+'Property'] = default_device_property_schema 


      # if the device is a sensor 
      if thing_type != 'actuator': 
        for i in range(len(tags)): # remove Actions tag 
          if (i==2):
            tags.pop(i)
      # if the device is an actuator 
      else:

        actions_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve a list of actions",
              "operationId": "retrieveWebThingActions",
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionsResponse"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

        }

        paths['/actions/'] = actions_endpoint

        for i in range(len(supported_actions)):
          device_action = supported_actions[i]
          retrieve_send_execution_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve recent executions of the "+device_action+" action",
              "description": "In response to an HTTP GET request on an Action URL, an Extended Web Thing must return an array that lists the recent executions of a specific Action.",
              "operationId": "retrieveRecentExecutionsOf"+device_action+"Action",
              "responses": {
                "200": {
                  "description": "successful operation",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/ActionExecution"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Actions"
              ],
              "summary": "Execute a(n) "+device_action+" action",
              "description": "In response to an HTTP POST request on an Action URL with valid parameters as request body, an Extended Web Thing must either reject the request with the appropriate status code or queue a task to run the action and return the status of that action in a 201 Created response. The action may not run immediately. The Location HTTP header identifies the URL to use to retrieve the most recent update on the action's status.",
              "operationId": "execute"+device_action_first_capital+"Action",
              "responses": {
                "204": {
                  "description": "NO RESPONSE"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/'+device_action] = retrieve_send_execution_endpoint

          retrieve_action_status_endpoint = {

            "get": {
              "tags": [
                "Actions"
              ],
              "summary": "Retrieve the status of a(n) "+device_action+" action",
              "description": "In response to an HTTP GET request on the URL targeted by the Location HTTP header returned in response to the request to execute an action, an Extended Web Thing must return the status of this action or a 404 Not Found status code if the action's status is no longer available.",
              "parameters": [
                {
                  "name": "executionId",
                  "in": "path",
                  "description": "action execution of Webthing to return",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "array",
                    "items": {
                      "type": "integer",
                      "format": "int64",
                      "default": 1
                    }
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/ActionExecution"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          paths['/actions/'+device_action+'/{executionId}'] = retrieve_action_status_endpoint

        # define general /actions schema 
        default_action_schema = {

          "required": [
            "id",
            "name"
          ],
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "example": "lock"
            },
            "name": {
              "type": "string",
              "example": "Lock the Smart Door"
            }
          },
          "xml": {
            "name": "Action"
          }
          
        }  

        default_action_execution_schema = {  

          "required": [
            "id",
            "status",
            "timestamp"
          ],
          "x-kindOf": "http://www.w3.org/ns/sosa/Actuation",
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "example": "223"
            },
            "status": {
              "type": "string",
              "example": "completed"
            },
            "timestamp": {
              "type": "string",
              "format": "date-time"
            }
          },
          "xml": {
            "name": "ActionExecution"
          }

        }   

        # define (default) ActionsResponse schema
        actions_jsonobj = {
          "anyOf": [           
            { 
              "$ref": "#/components/schemas/Action"
            }
          ],
          "xml": {
            "name": "ActionsResponse"
          }
        }     

        # append (default) ActionsResponse schema to schemas
        schemas['ActionsResponse'] = actions_jsonobj

        ### action schema ###

        # read action schema (if any) from user input to replace the default one
        action_schema = req.get("action_schema")
        if action_schema: 
          # append action Schema object to schemas
          schemas['Action'] = action_schema
        else: 
          # append action Schema object to schemas
          schemas['Action'] = default_action_schema

        ### action execution schema ###

        # read action execution schema (if any) from user input to replace the default one
        action_execution_schema = req.get("action_execution_schema")    
        if action_execution_schema: 
          # append action execution Schema object to schemas   
          schemas['ActionExecution'] = action_execution_schema
        else: 
          # append action execution Schema object to schemas
          schemas['ActionExecution'] = default_action_execution_schema      


        if sub_support=='yes':

          subscriptions_endpoints = {
            
            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve a list of subscriptions",
              "description": "In response to an HTTP GET request on the destination URL of a subscriptions link, an Extended Web Thing must return the array of subscriptions to the underlying resource.",
              "operationId": "retrieveListOfSubscriptions",
              "parameters": [
                {
                  "$ref": "#/components/parameters/pageParam"
                },
                {
                  "name": "perPage",
                  "description": "Pagination second (per page) parameter",
                  "in": "query",
                  "required": bool(False),
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "array",
                        "items": {
                          "$ref": "#/components/schemas/SubscriptionObject"
                        }
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "post": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Create a subscription",
              "description": "An Extended Web Thing should support subscriptions for the specific resource (DHT22).",
              "operationId": "createSubscription",
              "x-operationType": "https://schema.org/CreateAction",
              "requestBody": {
                "description": "Create a new subscription",
                "content": {
                  "application/json": {
                    "schema": {
                      "$ref": "#/components/schemas/SubscriptionRequestBody"
                    }
                  }
                },
                "required": bool(True)
              },
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }
          
          } 

          #append /subscriptions endpoints and operations
          paths['/subscriptions/'] = subscriptions_endpoints

          # define /{subscriptionID} endpoints 
          subscriptionID_endpoints = { 

            "get": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Retrieve information about a specific subscription",
              "description": "In response to an HTTP GET request on a Subscription URL, an Extended Web Thing must return a JSON representation of the subscription. The JSON representation should be the same as the one returned for that subscription in 'Retrieve a list of subscriptions'.",
              "operationId": "retreiveInfoAboutSubscription",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "x-mapsTo": "#/components/schemas/SubscriptionObject.id",
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK",
                  "content": {
                    "application/json": {
                      "schema": {
                        "$ref": "#/components/schemas/SubscriptionObject"
                      }
                    }
                  }
                },
                "404": {
                  "description": "Not found"
                }
              }
            },
            "delete": {
              "tags": [
                "Subscriptions"
              ],
              "summary": "Delete a subscription",
              "description": "In response to an HTTP DELETE request on the destination URL of a subscriptions an Extended Web Thing must either reject  the request with an appropriate status code or remove (unsubscribe) the subscription and return a 200 OK status code.",
              "operationId": "deleteSubscription",
              "x-operationType": "https://schema.org/DeleteAction",
              "parameters": [
                {
                  "name": "subscriptionID",
                  "in": "path",
                  "description": "The id of the specific subscription",
                  "required": bool(True),
                  "style": "simple",
                  "explode": bool(True),
                  "schema": {
                    "type": "string",
                    "example": "5fd23faccde6be05da68bcfb"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "OK"
                },
                "404": {
                  "description": "Not found"
                }
              }
            }

          }

          #append /subscriptions/{subscriptionID} endpoints and operations
          paths['/subscriptions/{subscriptionID}'] = subscriptionID_endpoints   

          #define subscription schemas 
          subscriptionRequestBody = {

            "required": [
              "description",
              "type",
              "callbackUrl",
              "resource"
            ],
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "example": "My subscription for SmartDoor's current state"
              },
              "description": {
                "type": "string",
                "example": "A subscription to get info about SmartDoor's current state"
              },
              "type": {
                "type": "string",
                "example": "webhook (callback)"
              },
              "callbackUrl": {
                "type": "string",
                "example": "http://172.16.1.5:5000/accumulate"
              },
              "resource": {
                "type": "object",
                "properties": {
                  "type": {
                    "type": "string",
                    "example": "property"
                  },
                  "name": {
                    "type": "string",
                    "example": "state"
                  }
                }
              },
              "expires": {
                "type": "string",
                "format": "date-time"
              },
              "throttling": {
                "type": "integer",
                "format": "int32",
                "example": 5
              }
            },
            "xml": {
              "name": "SubscriptionRequestBody"
            }
          }

          subscriptionObject = {

            "allOf": [
              {
                "required": [
                  "id",
                  "type",
                  "resource",
                  "description",
                  "callbackUrl"
                ],
                "type": "object",
                "properties": {
                  "id": {
                    "type": "string",
                    "example": "5fc978fc96cc26a4e202c3d6"
                  }
                }
              },
              {
                "$ref": "#/components/schemas/SubscriptionRequestBody"
              }
            ],
            "xml": {
              "name": "SubscriptionObject"
            }
          } 

          # append subscription Schema objects to schemas 
          schemas['SubscriptionRequestBody'] = subscriptionRequestBody
          schemas['SubscriptionObject'] = subscriptionObject

        else:
          for i in range(len(tags)): # remove Subscriptions tag 
            if (i==3):
              tags.pop(i)

      parameters = {
        
        "pageParam": {
          "name": "page",
          "description": "Pagination first (page) parameter",
          "in": "query",
          "required": bool(False),
          "schema": {
            "type": "integer"
          }
        }

      }

      # append tags to the description 
      td['tags'] = tags 
      # append paths to the description 
      td['paths'] = paths 
      
      componentsObject = {} # initialize Components object
      componentsObject['schemas'] = schemas
      componentsObject['parameters'] = parameters 

      if securitySchemes:
        componentsObject['securitySchemes'] = security_Schemes  # append securitySchemes to Components object 
      else: 
        componentsObject['securitySchemes'] = {} # append securitySchemes to Components object 

      td['components'] = componentsObject # append Components object to the document 

    with open('output.json', 'w') as json_file:
      json.dump(td, json_file, indent = 1)

    return td

    
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5000, debug=True)

