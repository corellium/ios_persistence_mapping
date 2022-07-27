const { Corellium } = require("corellium-api");
const process = require('process');

const config_data = require('./config.json');

async function main() {
    // Configure the API.
    let corellium = new Corellium({
        endpoint: config_data.endpoint,
        username: config_data.username,
        password: config_data.password
    });

    await corellium.login();

    let projects = await corellium.projects();
    let project = projects.find((project) => project.name === config_data.project);
    let instances = await project.instances();

    let instance = instances.find(
        (instance) => instance.id === config_data.instance,
    );

    let agent = await instance.newAgent();
    await agent.ready();
    
    try {
        let result = await agent.stat(process.argv[2]);
        console.log(JSON.stringify(result));
    } catch(err) {
        console.log('NotFound')
    }

    await agent.disconnect();
}

main().catch((err) => {
    console.error(err);
});
