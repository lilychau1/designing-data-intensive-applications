from single_leader_replication.storage import Storage
from single_leader_replication.replication_log import ReplicationLog
from single_leader_replication.node import Node
from single_leader_replication.models import LogEntry
from single_leader_replication.cluster import Cluster

# Initialize storage and log
storage = Storage()
log = ReplicationLog()

# Test applying log entries to storage
print('======================================================================================')
print('Test setting and getting values from storage using log entries')
print('======================================================================================')
print('\n')

entry1 = log.append('SET', 'foo', 'bar')
storage.apply_log_entry(entry1)

print('> After applying first log entry, should print "bar":')
print(storage.get('foo'))  # Should print 'bar'
print('\n')

print('> Log entries after first append, should print "SET foo bar":')
print(log.entries)  # Should print the log entry for 'SET foo bar'

print('\n')
# Test applying another log entry
entry2 = log.append('SET', 'baz', 42)
storage.apply_log_entry(entry2)

print('> After applying second log entry, should print "baz":')
print(storage.get('baz'))  # Should print 42

print('\n')

print('> Log entries after second append, should show "SET foo bar" and "SET baz 42":')

print(log.entries)  # Should print the log entry for 'SET baz 42'
print('\n')


# Test crash by deleting memory
print('======================================================================================')
print('Simulating crash and restart')
print('======================================================================================')
print('\n')

storage = Storage()
print('> After crash, should print None:')
print(storage.get('foo'))  # Should print None, simulating a crash and restart
print('\n')

# Test replaying log entries after a crash
for entry in log.entries:
    storage.apply_log_entry(entry)

print('> After replaying log entries, should print "bar" and 42:')
print(storage.get('foo'))  # Should print 'bar'
print(storage.get('baz'))  # Should print 42

# Test follower node receiving log entries when write is made to leader
print('======================================================================================')
print('Test follower node receiving log entries when write is made to leader')
print('======================================================================================')
print('\n')

leader = Node('leader')
follower = Node()

leader.add_follower(follower)

leader.write('foo', 'bar')
print('> After leader writes "foo", should print "bar":')
print(leader.read('foo'))  # Should print 'bar' 
print('\n')

print('> After leader writes "foo" and follower receives log entry, should print "bar":')
print(follower.read('foo'))  # Should print 'bar'
print('\n')

follower.receive_log_entry(LogEntry(index=1, operation='SET', key='baz', value=42))  # Simulate receiving a log with the same index as the last applied log entry
print('> After follower receives log entry with same index (but with key = "baz", value = 42), reading "foo" should print "bar":')
print(follower.read('foo'))  # Should still print 'bar'
print('\n')

print('> Reading "baz" should print None:')
print(follower.read('baz'))  # Should print None, as the log entry with the same index was ignored
print('\n')

e1 = leader.write("a", 1)
e2 = leader.write("b", 2)
print('> After leader writes "a" and "b", should print 1 and 2:')
print(leader.read("a"))  # Should print 1
print(leader.read("b"))  # Should print 2
print('\n')

print('After writing "a" and "b" to leader, attempt to apply log entry with index 1 to follower (should raise value error):')
try:
    follower.receive_log_entry(e2)
except Exception as e:
    print(f"Error: {e}")


# Test multiple follower nodes receiving log entries when write is made to single leader
print('======================================================================================')
print('Test MULTIPLE follower nodes receiving log entries when write is made to SINGLE leader')
print('======================================================================================')
print('\n')

leader = Node('leader')
follower_1 = Node()
follower_2 = Node()

leader.add_follower(follower_1)
leader.add_follower(follower_2)

leader.write('foo', 'bar')
print('> After leader writes "foo", should print "bar":')
print(leader.read('foo'))  # Should print 'bar'
print('\n')

# follower_1.receive_log_entry(log_entry)
# follower_2.receive_log_entry(log_entry)

print('> After followers receive log entry, should print "bar" and "bar":')
print(follower_1.read('foo'))  # Should print 'bar'
print(follower_2.read('foo'))  # Should print 'bar'
print('\n') 


# Test follower catching up after missing multiple log entries

print('======================================================================================')
print('Test follower catching up after missing multiple log entries')
print('======================================================================================')
print('\n')

leader = Node('leader')
follower = Node()

leader.add_follower(follower)

# Leader writes first entry, follower receives it
leader.write('a', 1)

print('> After first write, follower should have "a" = 1:')
print(follower.read('a'))
print('\n')

# Simulate follower falling behind by removing it from replication
leader._followers = []

leader.write('b', 2)
leader.write('c', 3)

print('> Follower missed "b" and "c", should print None:')
print(follower.read('b'))
print(follower.read('c'))
print('\n')

# Reconnect follower
leader.add_follower(follower)

leader.write('d', 4)

print('> After reconnecting, follower should catch up with all missing entries:')
print(follower.read('b'))  # Should print 2
print(follower.read('c'))  # Should print 3
print(follower.read('d'))  # Should print 4
print('\n')


# Test duplicate log entry handling

print('======================================================================================')
print('Test follower ignoring duplicate log entries')
print('======================================================================================')
print('\n')

leader = Node('leader')
follower = Node()

leader.add_follower(follower)

entry = leader.write('foo', 'bar')

print('> Before duplicate, follower should print "bar":')
print(follower.read('foo'))
print('\n')

# Send same entry again
follower.receive_log_entry(entry)

print('> After duplicate entry, follower should still print "bar":')
print(follower.read('foo'))

print('> Follower last applied index should still be 1:')
print(follower.last_applied_index)
print('\n')


# Test multiple followers staying synchronized

print('======================================================================================')
print('Test multiple followers staying synchronized')
print('======================================================================================')
print('\n')

leader = Node('leader')
followers = [
    Node(),
    Node(),
    Node()
]

for follower in followers:
    leader.add_follower(follower)

leader.write('x', 100)
leader.write('y', 200)
leader.write('z', 300)

print('> All followers should have x=100, y=200, z=300:')

for index, follower in enumerate(followers):
    print(f'Follower {index + 1}:')
    print(follower.read('x'))
    print(follower.read('y'))
    print(follower.read('z'))
    print('\n')
    
print('======================================================================================')
print('Test leader failover')
print('======================================================================================')
print('\n')


# Create nodes
node_1 = Node()
node_2 = Node()
node_3 = Node()


# Create cluster with node_1 as leader
cluster = Cluster(
    nodes=[
        node_1,
        node_2,
        node_3
    ],
    leader_node=node_1
)


print('> Initial leader should be node_1:')
print(cluster.leader is node_1)
print('\n')


# Write data through the leader

cluster.leader.write('foo', 'bar')

print('> Leader should contain foo=bar:')
print(node_1.read('foo'))

print('> Followers should contain replicated value:')
print(node_2.read('foo'))
print(node_3.read('foo'))
print('\n')


# Simulate leader failure

print('> Removing current leader...')
cluster.remove_node(node_1)

print('\n')


# Check new leader

print('> New leader should not be node_1:')
print(cluster.leader is not node_1)

print('> New leader should be node_2 or node_3:')
print(cluster.leader is node_2 or cluster.leader is node_3)

print('\n')


# Verify new leader still has old data

print('> New leader should still have old data foo=bar:')
print(cluster.leader.read('foo'))

print('\n')


# Write through the new leader

cluster.leader.write('baz', 123)

print('> New leader should contain baz=123:')
print(cluster.leader.read('baz'))

print('\n')


# Find the remaining follower

remaining_nodes = [
    node for node in cluster.nodes
    if node is not cluster.leader
]


print('> Remaining follower should receive new write:')
print(remaining_nodes[0].read('baz'))