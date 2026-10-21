// Loads the browser bundle (data.js + ses.js) into Node for testing.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const site = process.env.SES_SITE || path.join(__dirname, "..", "..", "_site");

function load(file = "data.js") {
    const sandbox = {window: {}};
    vm.runInNewContext(fs.readFileSync(path.join(site, "static", "js", file), "utf8"), sandbox);
    const create = require(path.join(__dirname, "..", "..", "static", "js", "ses.js"));
    return create(sandbox.window.SES_DATA);
}

module.exports = {load};
