import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import {
  Button,
  Dimmer,
  Divider,
  Grid,
  Header,
  Icon,
  Image,
  Label,
  Loader,
  Menu,
  Segment,
  Sidebar,
  Statistic,
  Table,
} from 'semantic-ui-react';
import { chartColors, syslogFacility, syslogSeverity } from './ui_support';

const version = 'ver.0.2';
const serverDataEntry = 'https://127.0.0.1:3000/server_data';
const serverEventsEntry = 'https://127.0.0.1:3000/server_events';
// const serverDataEntry = '/server_data';
// const serverEventsEntry = '/server_events';

const https = require('https');

function Narwhal() {
  const [eventsReady, setEventsReady] = useState(false);
  const [logDataJSON, setLogDataJSON] = useState();
  const [events, setEvents] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timerCounter, setTimerCounter] = useState(0);

  const [activeMenuItem, setActiveMenuItem] = useState('dashboard');

  useEffect(() => {
    const requestInstance = axios.create({
      httpsAgent: new https.Agent({
        keepAlive: true,
        rejectUnauthorized: false,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'PUT, GET, POST, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Origin, Accept, Content-Type, X-Requested-With',
        },
      }),
    });

    function fetchData(url) {
      requestInstance
        .get(url)
        .then((response) => {
          setLogDataJSON(JSON.parse(response.request.responseText));
        })
        .catch((error) => {
          // eslint-disable-next-line no-console
          console.log(error);
        });
    }

    function fetchEvents(url) {
      requestInstance
        .get(url)
        .then((response) => {
          setEvents(JSON.parse(response.request.responseText));
          setEventsReady(true);
        })
        .catch((error) => {
          // eslint-disable-next-line no-console
          console.log(error);
        });
    }

    function tick() {
      let counter = timerCounter + 1;
      if (counter === 1) {
        setLoading(true);
        fetchData(serverDataEntry);
        fetchEvents(serverEventsEntry);
        if (logDataJSON) {
          setLoading(false);
        }
      }
      if (counter === 30) {
        counter = 0;
      }
      setTimerCounter(counter);
    }

    const timerID = setInterval(() => tick(), 1000);

    return function cleanup() {
      clearInterval(timerID);
    };
  });

  const clickOnSideSectionMenuItem = (e, { value }) => {
    setActiveMenuItem(value);
  };

  const noticeColor = 'green';
  const warningColor = 'yellow';
  const alertColor = 'red';

  const projectTitle = (
    <Header inverted>
      <Image src="/public/nlogo.png" verticalAlign="middle" size="medium" />
      <Header.Content>
        Narwhal
        <Header.Subheader>{version}</Header.Subheader>
      </Header.Content>
    </Header>
  );

  function eventsTable() {
    let logTableRow = [];
    if (eventsReady === true) {
      for (let i = 0; i < events.dt.length; i += 1) {
        let recordDotColor = 'yellow';
        if (events.severity[i] < 4) {
          recordDotColor = 'red';
        }
        if (events.severity[i] === 5) {
          recordDotColor = 'green';
        }
        if (events.severity[i] === 6) {
          recordDotColor = 'blue';
        }
        if (events.severity[i] === 7) {
          recordDotColor = 'grey';
        }
        logTableRow[i] = (
          <Table.Row key={`eventTableRow${i}`}>
            <Table.Cell>
              <Label circular color={recordDotColor}>
                <b>{events.n[i]}</b>
              </Label>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny">
                <Header.Content>
                  {syslogSeverity[events.severity[i]].text}
                  <Header.Subheader>{syslogFacility[events.facility[i]].text}</Header.Subheader>
                </Header.Content>
              </Header>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny">
                <Header.Content>
                  {events.timestamp[i]}
                  <Header.Subheader>{events.dt[i]}</Header.Subheader>
                </Header.Content>
              </Header>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny">
                <Header.Content>
                  {events.ip[i]}
                  <Header.Subheader>{events.endpoint[i]}</Header.Subheader>
                </Header.Content>
              </Header>
            </Table.Cell>
            <Table.Cell>
              <Header size="tiny">
                <Header.Content>
                  {events.system[i]}
                  <Header.Subheader>{events.event[i]}</Header.Subheader>
                </Header.Content>
              </Header>
            </Table.Cell>
          </Table.Row>
        );
      }
    } else {
      logTableRow = null;
    }
    return (
      <Segment basic padded={false}>
        <Table compact="very" striped selectable size="small">
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell> N </Table.HeaderCell>
              <Table.HeaderCell> Sev/Facility </Table.HeaderCell>
              <Table.HeaderCell> Timestamp/Received at </Table.HeaderCell>
              <Table.HeaderCell> Source/Endpoint </Table.HeaderCell>
              <Table.HeaderCell> System / Message </Table.HeaderCell>
            </Table.Row>
          </Table.Header>

          <Table.Body>{logTableRow}</Table.Body>
        </Table>
      </Segment>
    );
  }

  if (!loading) {
    let renderSelectedMenuSection = '';

    if (activeMenuItem === 'dashboard') {
      renderSelectedMenuSection = (
        <Grid stretched padded relaxed="very">
          <Grid.Column mobile={16} tablet={13} computer={14} id="content">
            <Grid.Row>
              <Grid padded relaxed columns="equal">
                <Grid.Column>
                  <Statistic.Group size="small">
                    <Statistic>
                      <Statistic.Value>{logDataJSON.total_events}</Statistic.Value>
                      <Statistic.Label> log entries </Statistic.Label>
                    </Statistic>
                    <Statistic color={alertColor}>
                      <Statistic.Value>{logDataJSON.logAlertCount}</Statistic.Value>
                      <Statistic.Label> alerts </Statistic.Label>
                    </Statistic>
                    <Statistic color={warningColor}>
                      <Statistic.Value>{logDataJSON.logWarningsCount}</Statistic.Value>
                      <Statistic.Label> warnings </Statistic.Label>
                    </Statistic>
                    <Statistic color={noticeColor}>
                      <Statistic.Value>{logDataJSON.logMessageCount}</Statistic.Value>
                      <Statistic.Label> messages </Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Grid.Column>
                <Grid.Column>
                  <Statistic.Group size="small">
                    <Statistic>
                      <Statistic.Value>{logDataJSON.messages_per_second}</Statistic.Value>
                      <Statistic.Label> msg / sec </Statistic.Label>
                    </Statistic>
                    <Statistic>
                      <Statistic.Value>{logDataJSON.seconds_between_messages}</Statistic.Value>
                      <Statistic.Label> avg.interval, sec. </Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Grid.Column>
                <Grid.Column>
                  <Statistic.Group size="small">
                    <Statistic>
                      <Statistic.Value>{logDataJSON.redis_used_memory_human}</Statistic.Value>
                      <Statistic.Label> used redis memory </Statistic.Label>
                    </Statistic>
                    <Statistic>
                      <Statistic.Value>
                        {logDataJSON.redis_total_system_memory_human}
                      </Statistic.Value>
                      <Statistic.Label> total redis memory </Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Grid.Column>
              </Grid>
            </Grid.Row>
            <Grid.Row>
              <ScatterChart
                height={250}
                width={1200}
                margin={{
                  top: 20,
                  right: 10,
                  bottom: 10,
                  left: 10,
                }}
              >
                <CartesianGrid />
                <XAxis type="category" dataKey="x" name="timeline" />
                <YAxis type="number" dataKey="y" name="severity" />
                <ZAxis type="number" dataKey="z" name="amount" unit="log records" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Legend />
                <Scatter
                  name={syslogSeverity[0].text}
                  data={logDataJSON.ChartData0}
                  fill={chartColors[0]}
                />
                <Scatter
                  name={syslogSeverity[1].text}
                  data={logDataJSON.ChartData1}
                  fill={chartColors[1]}
                />
                <Scatter
                  name={syslogSeverity[2].text}
                  data={logDataJSON.ChartData2}
                  fill={chartColors[2]}
                />
                <Scatter
                  name={syslogSeverity[3].text}
                  data={logDataJSON.ChartData3}
                  fill={chartColors[3]}
                />
                <Scatter
                  name={syslogSeverity[4].text}
                  data={logDataJSON.ChartData4}
                  fill={chartColors[4]}
                />
                <Scatter
                  name={syslogSeverity[5].text}
                  data={logDataJSON.ChartData5}
                  fill={chartColors[5]}
                />
                <Scatter
                  name={syslogSeverity[6].text}
                  data={logDataJSON.ChartData6}
                  fill={chartColors[6]}
                />
                <Scatter
                  name={syslogSeverity[7].text}
                  data={logDataJSON.ChartData7}
                  fill={chartColors[7]}
                />
              </ScatterChart>
            </Grid.Row>
            <Grid.Row>{eventsTable()}</Grid.Row>
          </Grid.Column>
        </Grid>
      );
    }
    if (activeMenuItem === 'data') {
      renderSelectedMenuSection = (
        <Grid columns={4} stackable textAlign="center" stretched padded relaxed="very">
          <Grid.Row>
            <Header padded>Export events data as</Header>
          </Grid.Row>
          <Grid.Row verticalAlign="middle">
            <Grid.Column />
            <Grid.Column>
              <Header icon>
                <Icon name="file excel outline" />
                CSV
              </Header>
              <Button>
                <a href="/csv_alerts">Alerts only</a>
              </Button>
              <Divider hidden />
              <Button>
                <a href="/csv_all">All events</a>
              </Button>
            </Grid.Column>
            <Grid.Column>
              <Header icon>
                <Icon name="file code outline" />
                JSON
              </Header>
              <Button>
                <a href="/json_alerts">Alerts only</a>
              </Button>
              <Divider hidden />
              <Button>
                <a href="/json_all">All events</a>
              </Button>
            </Grid.Column>
            <Grid.Column />
          </Grid.Row>
        </Grid>
      );
    }
    const sideMenu = (
      <>
        <Menu.Item header>{projectTitle}</Menu.Item>
        <Menu.Item header value="dashboard" onClick={clickOnSideSectionMenuItem}>
          <Icon name="heartbeat" size="large" />
          Dashboard
        </Menu.Item>
        <Menu.Item header value="data" onClick={clickOnSideSectionMenuItem}>
          <Icon name="book" size="large" />
          Data export
        </Menu.Item>
      </>
    );
    return (
      <Sidebar.Pushable as={Segment}>
        <Sidebar as={Menu} animation="slide along" inverted vertical visible width="thin">
          {sideMenu}
        </Sidebar>
        <Sidebar.Pusher>
          <Segment basic>{renderSelectedMenuSection}</Segment>
        </Sidebar.Pusher>
      </Sidebar.Pushable>
    );
  }
  return (
    <>
      <Dimmer inverted active={loading}>
        <Loader size="massive"> Loading </Loader>
      </Dimmer>
    </>
  );
}

export default Narwhal;
