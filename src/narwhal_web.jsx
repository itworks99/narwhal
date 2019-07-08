import { ResponsiveWaffle } from '@nivo/waffle';
import { LineChart } from 'react-chartkick';
import 'chart.js';
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
const serverData = 'https://localhost:3000/server_data';
const serverEvents = 'https://localhost:3000/server_events';

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
          console.log(error);
        });
    }

    function tick() {
      let counter = timerCounter + 1;
      if (counter === 1) {
        setLoading(true);
        fetchData(serverData);
        fetchEvents(serverEvents);
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
      <Image src="/nlogo.png" verticalAlign="middle" size="medium" />
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
        <Table compact="very" striped selectable>
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
    const waffleChartData = [
      {
        id: syslogSeverity[0].key,
        label: syslogSeverity[0].text,
        value: logDataJSON.sev0,
      },
      {
        id: syslogSeverity[1].key,
        label: syslogSeverity[1].text,
        value: logDataJSON.sev1,
      },
      {
        id: syslogSeverity[2].key,
        label: syslogSeverity[2].text,
        value: logDataJSON.sev2,
      },
      {
        id: syslogSeverity[3].key,
        label: syslogSeverity[3].text,
        value: logDataJSON.sev3,
      },
      {
        id: syslogSeverity[4].key,
        label: syslogSeverity[4].text,
        value: logDataJSON.sev4,
      },
      {
        id: syslogSeverity[5].key,
        label: syslogSeverity[5].text,
        value: logDataJSON.sev5,
      },
      {
        id: syslogSeverity[6].key,
        label: syslogSeverity[6].text,
        value: logDataJSON.sev6,
      },
      {
        id: syslogSeverity[7].key,
        label: syslogSeverity[7].text,
        value: logDataJSON.sev7,
      },
    ];

    const lineChartData = [
      {
        name: logDataJSON.chartDatasev0.name,
        data: logDataJSON.chartDatasev0.data,
      },
      {
        name: logDataJSON.chartDatasev1.name,
        data: logDataJSON.chartDatasev1.data,
      },
      {
        name: logDataJSON.chartDatasev2.name,
        data: logDataJSON.chartDatasev2.data,
      },
      {
        name: logDataJSON.chartDatasev3.name,
        data: logDataJSON.chartDatasev3.data,
      },
      {
        name: logDataJSON.chartDatasev4.name,
        data: logDataJSON.chartDatasev4.data,
      },
      {
        name: logDataJSON.chartDatasev5.name,
        data: logDataJSON.chartDatasev5.data,
      },
      {
        name: logDataJSON.chartDatasev6.name,
        data: logDataJSON.chartDatasev6.data,
      },
      {
        name: logDataJSON.chartDatasev7.name,
        data: logDataJSON.chartDatasev7.data,
      },
    ];

    let renderSelectedMenuSection = '';

    const logAlertCount = logDataJSON.sev0 + logDataJSON.sev1 + logDataJSON.sev2 + logDataJSON.sev3;
    const logMessageCount = logDataJSON.sev5 + logDataJSON.sev6 + logDataJSON.sev7;

    if (activeMenuItem === 'dashboard') {
      renderSelectedMenuSection = (
        <Grid stretched padded relaxed="very">
          <Grid.Column mobile={16} tablet={13} computer={14} id="content">
            <Grid.Row>
              <Grid padded relaxed columns="equal">
                <Grid.Column>
                  <Statistic.Group size="mini">
                    <Statistic>
                      <Statistic.Value>{logDataJSON.total_events}</Statistic.Value>
                      <Statistic.Label> log entries </Statistic.Label>
                    </Statistic>
                    <Statistic color={alertColor}>
                      <Statistic.Value>{logAlertCount}</Statistic.Value>
                      <Statistic.Label> alerts </Statistic.Label>
                    </Statistic>
                    <Statistic color={warningColor}>
                      <Statistic.Value>{logDataJSON.sev4}</Statistic.Value>
                      <Statistic.Label> warnings </Statistic.Label>
                    </Statistic>
                    <Statistic color={noticeColor}>
                      <Statistic.Value>{logMessageCount}</Statistic.Value>
                      <Statistic.Label> messages </Statistic.Label>
                    </Statistic>
                  </Statistic.Group>
                </Grid.Column>
                <Grid.Column>
                  <div
                    style={{
                      height: 40,
                    }}
                  >
                    <ResponsiveWaffle
                      data={waffleChartData}
                      total={logMessageCount}
                      rows={4}
                      columns={40}
                      padding={2}
                      margin={{
                        top: 2,
                        right: 2,
                        bottom: 2,
                        left: 2,
                      }}
                      colors={chartColors}
                      colorBy="id"
                      borderColor="inherit"
                      fillDirection="top"
                      animate={false}
                    />
                  </div>
                </Grid.Column>
                <Grid.Column>
                  <Statistic.Group size="mini">
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
                  <Statistic.Group size="mini">
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
              <LineChart
                xmin={logDataJSON.firstDataTimestamp}
                data={lineChartData}
                download
                colors={chartColors}
                curve
                legend="bottom"
                library={{
                  animation: { duration: 0 },
                  hover: { animationDuration: 0 },
                  responsiveAnimationDuration: 0,
                  legend: {
                    labels: {
                      boxWidth: 10,
                      defaultFontFamily: 'Lato',
                    },
                  },
                  elements: {
                    point: { radius: 1 },
                  },
                }}
              />
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
      <React.Fragment>
        <Menu.Item header>{projectTitle}</Menu.Item>
        <Menu.Item header value="dashboard" onClick={clickOnSideSectionMenuItem}>
          <Icon name="heartbeat" size="large" />
          Dashboard
        </Menu.Item>
        <Menu.Item header value="data" onClick={clickOnSideSectionMenuItem}>
          <Icon name="book" size="large" />
          Data export
        </Menu.Item>
      </React.Fragment>
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
    <React.Fragment>
      <Dimmer inverted active={loading}>
        <Loader size="massive"> Loading </Loader>
      </Dimmer>
    </React.Fragment>
  );
}

export default Narwhal;
