const { Corellium } = require("corellium-api");
const fs = require('fs');
const process = require('process');

const config_data = require('./config.json');

async function downloadFile(agent, remote_path, local_path) {
    return new Promise(resolve => {
        const dl = agent.download(remote_path);
        let b = fs.createWriteStream(local_path);
        b.on('finish', resolve);
        dl.pipe(b);
    });
}

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
    
    await downloadFile(agent, process.argv[2], process.argv[3]);
    
    await agent.disconnect();
}

main().catch((err) => {
    console.error(err);
});
