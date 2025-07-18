class AgenticGenerativeUIFlow(Flow[AgentState]):
    """
    This is a sample flow that uses the CopilotKit framework to create a chat agent.
    """

    
    @start()
    async def start_flow(self):
        """
        This is the entry point for the flow.
        """
        self.state.steps = []

    @router(or_(start_flow, "simulate_task"))
    async def chat(self):
        """
        Standard chat node.
        """
        system_prompt = """
        You are a helpful assistant assisting with any task. 
        When asked to do something, you MUST call the function `generate_task_steps`
        that was provided to you.
        If you called the function, you MUST NOT repeat the steps in your next response to the user.
        Just give a very brief summary (one sentence) of what you did with some emojis. 
        Always say you actually did the steps, not merely generated them.
        """

        # 1. Here we specify that we want to stream the tool call to generate_task_steps
        #    to the frontend as state.
        await copilotkit_predict_state({
            "steps": {
                "tool": "generate_task_steps",
                "tool_argument": "steps"
            }
        })

        # 2. Run the model and stream the response
        #    Note: In order to stream the response, wrap the completion call in
        #    copilotkit_stream and set stream=True.
        response = await copilotkit_stream(
            completion(

                # 2.1 Specify the model to use
                model="openai/gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    *self.state.messages
                ],

                # 2.2 Bind the tools to the model
                tools=[
                    *self.state.copilotkit.actions,
                    PERFORM_TASK_TOOL
                ],

                # 2.3 Disable parallel tool calls to avoid race conditions,
                #     enable this for faster performance if you want to manage
                #     the complexity of running tool calls in parallel.
                parallel_tool_calls=False,
                stream=True
            )
        )

        message = response.choices[0].message

        # 3. Append the message to the messages in state
        self.state.messages.append(message)

        # 4. Handle tool call
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            tool_call_id = tool_call["id"]
            tool_call_name = tool_call["function"]["name"]
            tool_call_args = json.loads(tool_call["function"]["arguments"])

            if tool_call_name == "generate_task_steps":
                # Convert each step in the JSON array to a TaskStep instance
                self.state.steps = [TaskStep(**step) for step in tool_call_args["steps"]]

                # 4.1 Append the result to the messages in state
                self.state.messages.append({
                    "role": "tool",
                    "content": "Steps executed.",
                    "tool_call_id": tool_call_id
                })
                return "route_simulate_task"

        # 5. If our tool was not called, return to the end route
        return "route_end"

    @listen("route_simulate_task")
    async def simulate_task(self):
        """
        Simulate the task.
        """
        for step in self.state.steps:
            # simulate executing the step
            await asyncio.sleep(1)
            step.status = "completed"
            await copilotkit_emit_state(self.state)

    @listen("route_end")
    async def end(self):
        """
        End the flow.
        """